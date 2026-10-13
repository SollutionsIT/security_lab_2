import { BadRequestException, NotFoundException, PayloadTooLargeException } from '@nestjs/common';
import { mkdtemp, rm, symlink, unlink, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import type { SecurityEventsService } from '../../security/security-events.service';
import { InMemoryRepository } from '../../data/in-memory.repository';
import { Role } from '../../data/entities';
import { MAX_UPLOAD_BYTES, type MultipartFile, UploadService } from './upload.service';

describe('UploadService', () => {
  let root: string;
  let service: UploadService;
  const actor = { id: 'user-alice', role: Role.User };

  beforeEach(async () => {
    root = await mkdtemp(join(tmpdir(), 'company-upload-test-'));
    const events = { record: jest.fn() } as unknown as SecurityEventsService;
    service = new UploadService({ storageRoot: root }, new InMemoryRepository(), events);
  });

  afterEach(async () => {
    await rm(root, { recursive: true, force: true });
  });

  function file(overrides: Partial<MultipartFile> = {}): MultipartFile {
    const buffer = Buffer.concat([
      Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
      Buffer.from('synthetic image bytes'),
    ]);
    return {
      originalname: 'image.png',
      mimetype: 'image/png',
      size: buffer.length,
      buffer,
      ...overrides,
    };
  }

  it('stores a valid file under a generated server-side name', async () => {
    const stored = await service.store(file(), actor, 'correlation-1234');
    expect(stored.storedName).toMatch(/^[0-9a-f-]+\.png$/);
    expect(stored.storedName).not.toContain('image');

    const downloaded = await service.download(stored.storedName, actor, 'correlation-1234');
    expect(downloaded.headers['Content-Disposition']).toBe(
      'attachment; filename="download.png"',
    );
    expect(downloaded.headers['X-Content-Type-Options']).toBe('nosniff');
  });

  it('rejects oversized files', async () => {
    const buffer = Buffer.alloc(MAX_UPLOAD_BYTES + 1, 0x41);
    await expect(
      service.store(file({ buffer, size: buffer.length }), actor, 'correlation-1234'),
    ).rejects.toBeInstanceOf(PayloadTooLargeException);
  });

  it.each([
    ['wrong MIME', { mimetype: 'application/pdf' }],
    ['extension/content mismatch', { originalname: 'image.pdf' }],
    ['path traversal', { originalname: '../image.png' }],
    ['backslash traversal', { originalname: '..\\image.png' }],
    ['unsupported type', { originalname: 'image.gif', mimetype: 'image/gif' }],
  ])('rejects %s', async (_label, overrides) => {
    await expect(
      service.store(file(overrides), actor, 'correlation-1234'),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('rejects empty files', async () => {
    await expect(
      service.store(file({ buffer: Buffer.alloc(0), size: 0 }), actor, 'correlation-1234'),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('does not permit traversal through the download name', async () => {
    await expect(
      service.download('../secret.pdf', actor, 'correlation-1234'),
    ).rejects.toBeInstanceOf(
      NotFoundException,
    );
  });

  it('conceals another owner attachment and emits an audit event', async () => {
    const events = { record: jest.fn() } as unknown as SecurityEventsService;
    const repository = new InMemoryRepository();
    service = new UploadService({ storageRoot: root }, repository, events);
    const stored = await service.store(file(), actor, 'correlation-create');

    await expect(
      service.download(
        stored.storedName,
        { id: 'user-bob', role: Role.User },
        'correlation-denied',
      ),
    ).rejects.toBeInstanceOf(NotFoundException);
    expect(events.record).toHaveBeenCalledWith(
      expect.objectContaining({
        event: 'authorization_denied',
        actorId: 'user-bob',
        resourceType: 'attachment',
        action: 'read',
      }),
    );
  });

  it('does not follow a symlink replacing a stored attachment', async () => {
    const stored = await service.store(file(), actor, 'correlation-create');
    const original = join(root, stored.storedName);
    const replacement = join(root, 'replacement.png');
    await writeFile(replacement, file().buffer);
    await unlink(original);
    await symlink(replacement, original);
    await expect(service.download(stored.storedName, actor, 'correlation-read'))
      .rejects.toBeInstanceOf(NotFoundException);
  });
});
