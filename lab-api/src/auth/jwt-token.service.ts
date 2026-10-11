import { Inject, Injectable, UnauthorizedException } from '@nestjs/common';
import { jwtVerify, SignJWT } from 'jose';
import { APP_CONFIG, AppConfig } from '../config/app-config';
import { AuthenticatedActor, Role } from '../data/entities';

@Injectable()
export class JwtTokenService {
  private readonly key: Uint8Array;

  constructor(@Inject(APP_CONFIG) private readonly config: AppConfig) {
    this.key = new TextEncoder().encode(config.jwt.secret);
  }

  async issue(actor: AuthenticatedActor): Promise<string> {
    return new SignJWT({ role: actor.role })
      .setProtectedHeader({ alg: 'HS256', typ: 'JWT' })
      .setSubject(actor.id)
      .setIssuer(this.config.jwt.issuer)
      .setAudience(this.config.jwt.audience)
      .setIssuedAt()
      .setExpirationTime(`${this.config.jwt.ttlSeconds}s`)
      .sign(this.key);
  }

  async verify(token: string): Promise<AuthenticatedActor> {
    try {
      const { payload, protectedHeader } = await jwtVerify(token, this.key, {
        algorithms: ['HS256'],
        issuer: this.config.jwt.issuer,
        audience: this.config.jwt.audience,
        maxTokenAge: `${this.config.jwt.ttlSeconds}s`,
        clockTolerance: 5,
      });
      if (
        protectedHeader.alg !== 'HS256' ||
        protectedHeader.typ !== 'JWT' ||
        typeof payload.sub !== 'string' ||
        typeof payload.iat !== 'number' ||
        typeof payload.exp !== 'number' ||
        payload.exp <= payload.iat ||
        !Object.values(Role).includes(payload.role as Role)
      ) {
        throw new Error('Token claims are incomplete');
      }
      return { id: payload.sub, role: payload.role as Role };
    } catch {
      throw new UnauthorizedException('Unauthorized');
    }
  }
}
