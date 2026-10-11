import type { NextFunction, Request, Response } from 'express';
import { randomUUID } from 'node:crypto';
import type { LabRequest } from './lab-request';

const SAFE_CORRELATION_ID = /^[A-Za-z0-9_-]{8,64}$/;

export function correlationIdMiddleware(
  request: Request,
  response: Response,
  next: NextFunction,
): void {
  const labRequest = request as LabRequest;
  const supplied = request.header('x-correlation-id');
  labRequest.correlationId = supplied && SAFE_CORRELATION_ID.test(supplied)
    ? supplied
    : randomUUID();
  response.setHeader('x-correlation-id', labRequest.correlationId);
  next();
}
