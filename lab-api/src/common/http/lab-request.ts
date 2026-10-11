import type { Request } from 'express';
import type { AuthenticatedActor } from '../../data/entities';

export interface LabRequest extends Request {
  correlationId: string;
  actor?: AuthenticatedActor;
}
