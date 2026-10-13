import {
  BadRequestException,
  Inject,
  Injectable,
  NotFoundException,
  PayloadTooLargeException,
} from '@nestjs/common';
import { randomUUID } from 'node:crypto';
import { constants } from 'node:fs';
import { mkdir, open, readdir, unlink, writeFile } from 'node:fs/promises';
import { extname, isAbsolute, join, relative, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { AuthenticatedActor, Role } from '../../data/entities';
import { InMemoryRepository } from '../../data/in-memory.repository';
import { SecurityEventsService } from '../../security/security-events.service';

export const UPLOAD_CONFIG = Symbol('UPLOAD_CONFIG');
export const MAX_UPLOAD_BYTES = 1_048_576;

export interface UploadConfig {
  readonly storageRoot: string;
}

export interface MultipartFile {
  readonly originalname: string;
  readonly mimetype: string;
  readonly size: number;
  readonly buffer: Buffer;
}

export interface StoredUpload {
  readonly attachmentId: string;
  readonly storedName: string;
  readonly mediaType: 'image/png' | 'application/pdf';
  readonly sizeBytes: number;
}

export interface SafeDownload {
  readonly body: Buffer;
  readonly headers: Readonly<Record<string, string>>;
}

const FORMATS = Object.freeze({
  '.png': {
    mediaType: 'image/png' as const,
    matches: (buffer: Buffer): boolean =>
      buffer.length >= 8 &&
      buffer.subarray(0, 8).equals(
        Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
      ),
  },
  '.pdf': {
    mediaType: 'application/pdf' as const,
    matches: (buffer: Buffer): boolean =>
      buffer.length >= 5 && buffer.subarray(0, 5).equals(Buffer.from('%PDF-', 'ascii')),
  },
});

type AllowedExtension = keyof typeof FORMATS;

function isInside(parent: string, candidate: string): boolean {
  const pathFromParent = relative(parent, candidate);
  return pathFromParent !== '' && !pathFromParent.startsWith('..') && !isAbsolute(pathFromParent);
}

function assertSafeRoot(configuredRoot: string): string {
  const root = resolve(configuredRoot);
  const systemTemporaryRoot = resolve(tmpdir());
  if (!isInside(systemTemporaryRoot, root)) {
    throw new Error('UPLOAD_STORAGE_ROOT must be a dedicated directory under the system temporary root');
  }
  return root;
}

function extensionOf(originalName: string): AllowedExtension {
  if (
    !originalName ||
    originalName.includes('\0') ||
    originalName.includes('/') ||
    originalName.includes('\\')
  ) {
    throw new BadRequestException('Client filename is unsafe');
  }
  const extension = extname(originalName).toLowerCase();
  if (extension === '.png') return '.png';
  if (extension === '.pdf') return '.pdf';
  throw new BadRequestException('File extension is not allowed');
}

@Injectable()
export class UploadService {
  private readonly storageRoot: string;

  constructor(
    @Inject(UPLOAD_CONFIG) config: UploadConfig,
    private readonly repository: InMemoryRepository,
    private readonly securityEvents: SecurityEventsService,
  ) {
    this.storageRoot = assertSafeRoot(config.storageRoot);
  }

  async store(
    file: MultipartFile | undefined,
    actor: AuthenticatedActor,
    correlationId: string,
  ): Promise<StoredUpload> {
    if (!file) {
      throw new BadRequestException('A single upload file is required');
    }
    if (!Buffer.isBuffer(file.buffer) || file.buffer.length === 0 || file.size === 0) {
      throw new BadRequestException('Empty files are not allowed');
    }
    if (file.size !== file.buffer.length) {
      throw new BadRequestException('File size metadata does not match its content');
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      throw new PayloadTooLargeException(`File exceeds ${MAX_UPLOAD_BYTES} bytes`);
    }

    const extension = extensionOf(file.originalname);
    const format = FORMATS[extension];
    if (file.mimetype !== format.mediaType) {
      throw new BadRequestException('File MIME type does not match its extension');
    }
    if (!format.matches(file.buffer)) {
      throw new BadRequestException('File content does not match its declared type');
    }

    const attachmentId = randomUUID();
    const storedName = `${attachmentId}${extension}`;
    const target = resolve(this.storageRoot, storedName);
    if (!isInside(this.storageRoot, target)) {
      throw new BadRequestException('Upload path is invalid');
    }

    await mkdir(this.storageRoot, { recursive: true, mode: 0o700 });
    await writeFile(target, file.buffer, { flag: 'wx', mode: 0o600 });
    this.repository.saveAttachment({
      id: attachmentId,
      ownerId: actor.id,
      propertyId: 'unassigned',
      filename: storedName,
      mediaType: format.mediaType,
      sizeBytes: file.size,
      storageKey: storedName,
      createdAt: new Date().toISOString(),
    });
    this.securityEvents.record({
      event: 'file_upload_accepted',
      resourceType: 'attachment',
      resourceId: attachmentId,
      action: 'create',
      result: 'accepted',
      correlationId,
      metadata: { media_type: format.mediaType, size_bytes: file.size },
    });

    return {
      attachmentId,
      storedName,
      mediaType: format.mediaType,
      sizeBytes: file.size,
    };
  }

  async download(
    storedName: string,
    actor: AuthenticatedActor,
    correlationId: string,
  ): Promise<SafeDownload> {
    const match = /^([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})(\.png|\.pdf)$/i.exec(
      storedName,
    );
    if (!match) {
      throw new NotFoundException('Attachment not found');
    }
    const extension = match[2]?.toLowerCase() as AllowedExtension | undefined;
    if (!extension || !(extension in FORMATS)) {
      throw new NotFoundException('Attachment not found');
    }
    const attachment = this.repository.findAttachmentByStorageKey(storedName);
    if (
      !attachment ||
      (actor.role !== Role.Admin && attachment.ownerId !== actor.id)
    ) {
      if (attachment) {
        this.securityEvents.record({
          event: 'authorization_denied',
          actorId: actor.id,
          resourceType: 'attachment',
          resourceId: attachment.id,
          action: 'read',
          result: 'denied',
          correlationId,
          reason: 'owner_role_policy',
        });
      }
      throw new NotFoundException('Attachment not found');
    }
    const target = resolve(this.storageRoot, attachment.storageKey);
    if (!isInside(this.storageRoot, target)) {
      throw new NotFoundException('Attachment not found');
    }

    try {
      // Open the server-owned storage key once; do not follow a swapped symlink
      // between a path-based lstat and a separate path-based read.
      const handle = await open(target, constants.O_RDONLY | constants.O_NOFOLLOW);
      let body: Buffer;
      try {
        const status = await handle.stat();
        if (!status.isFile() || status.size > MAX_UPLOAD_BYTES) {
          throw new NotFoundException('Attachment not found');
        }
        body = await handle.readFile();
      } finally {
        await handle.close();
      }
      if (!FORMATS[extension].matches(body)) {
        throw new NotFoundException('Attachment not found');
      }
      return {
        body,
        headers: Object.freeze({
          'Content-Type': FORMATS[extension].mediaType,
          'Content-Disposition': `attachment; filename="download${extension}"`,
          'Content-Length': String(body.length),
          'X-Content-Type-Options': 'nosniff',
          'Content-Security-Policy': "default-src 'none'; sandbox",
          'Cache-Control': 'private, no-store',
        }),
      };
    } catch (error) {
      if (error instanceof NotFoundException) {
        throw error;
      }
      throw new NotFoundException('Attachment not found');
    }
  }

  /** Test-support cleanup. The constructor already confines this root to OS temp. */
  async clearStorage(): Promise<void> {
    let entries: string[];
    try {
      entries = await readdir(this.storageRoot);
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === 'ENOENT') return;
      throw error;
    }
    await Promise.all(
      entries
        .filter((entry) => /^[0-9a-f-]{36}\.(png|pdf)$/i.test(entry))
        .map(async (entry) => unlink(resolve(this.storageRoot, entry))),
    );
  }
}

export function defaultUploadConfig(): UploadConfig {
  return {
    storageRoot:
      process.env.UPLOAD_STORAGE_ROOT ?? join(tmpdir(), 'company-security-lab-uploads'),
  };
}
