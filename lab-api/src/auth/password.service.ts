import { Injectable } from '@nestjs/common';
import {
  randomBytes,
  scrypt as nodeScrypt,
  scryptSync,
  timingSafeEqual,
} from 'node:crypto';
const ALGORITHM = 'scrypt';
const COST = 16_384;
const BLOCK_SIZE = 8;
const PARALLELIZATION = 1;
const KEY_LENGTH = 64;
const MAX_MEMORY = 64 * 1024 * 1024;

function derive(password: string, salt: Buffer): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    nodeScrypt(
      password,
      salt,
      KEY_LENGTH,
      { N: COST, r: BLOCK_SIZE, p: PARALLELIZATION, maxmem: MAX_MEMORY },
      (error, derivedKey) => {
        if (error) reject(error);
        else resolve(derivedKey);
      },
    );
  });
}

function encodeHash(salt: Buffer, digest: Buffer): string {
  return [
    ALGORITHM,
    COST,
    BLOCK_SIZE,
    PARALLELIZATION,
    salt.toString('base64url'),
    digest.toString('base64url'),
  ].join('$');
}

export function createDeterministicSeedHash(password: string, saltText: string): string {
  const salt = Buffer.from(saltText, 'utf8');
  const digest = scryptSync(password, salt, KEY_LENGTH, {
    N: COST,
    r: BLOCK_SIZE,
    p: PARALLELIZATION,
    maxmem: MAX_MEMORY,
  });
  return encodeHash(salt, digest);
}

@Injectable()
export class PasswordService {
  async hash(password: string): Promise<string> {
    const salt = randomBytes(16);
    const digest = await derive(password, salt);
    return encodeHash(salt, digest);
  }

  async verify(password: string, encoded: string): Promise<boolean> {
    const [algorithm, cost, blockSize, parallelization, saltText, digestText] =
      encoded.split('$');

    if (
      algorithm !== ALGORITHM ||
      Number(cost) !== COST ||
      Number(blockSize) !== BLOCK_SIZE ||
      Number(parallelization) !== PARALLELIZATION ||
      !saltText ||
      !digestText
    ) {
      return false;
    }

    try {
      const salt = Buffer.from(saltText, 'base64url');
      const expected = Buffer.from(digestText, 'base64url');
      if (salt.length < 16 || expected.length !== KEY_LENGTH) {
        return false;
      }
      const actual = await derive(password, salt);
      return timingSafeEqual(actual, expected);
    } catch {
      return false;
    }
  }
}
