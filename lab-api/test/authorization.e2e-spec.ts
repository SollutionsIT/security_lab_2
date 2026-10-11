import type { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../src/app.module';
import { configureApplication } from '../src/bootstrap';
import { InMemoryRepository } from '../src/data/in-memory.repository';
import { SecurityEventsService } from '../src/security/security-events.service';

describe('authorization security contract', () => {
  let app: INestApplication;
  let repository: InMemoryRepository;
  let securityEvents: SecurityEventsService;

  beforeEach(async () => {
    process.env.NODE_ENV = 'test';
    process.env.JWT_SECRET = 'synthetic-test-signing-key-at-least-32-characters';
    process.env.LAB_TEST_MODE = 'true';
    process.env.LAB_TEST_KEY = 'synthetic-local-test-key';
    const moduleRef = await Test.createTestingModule({ imports: [AppModule] }).compile();
    app = moduleRef.createNestApplication({ bodyParser: false });
    configureApplication(app);
    await app.init();
    repository = moduleRef.get(InMemoryRepository);
    securityEvents = moduleRef.get(SecurityEventsService);
  });

  afterEach(async () => {
    await app.close();
  });

  async function login(email: string, password: string): Promise<string> {
    const response = await request(app.getHttpServer())
      .post('/auth/login')
      .send({ email, password })
      .expect(200);
    return response.body.accessToken as string;
  }

  it('conceals and audits cross-owner property access without a side effect', async () => {
    const token = await login('bob@example.test', 'Bob-Local-Only!42');
    const before = repository.getProperty('property-alice');

    const response = await request(app.getHttpServer())
      .patch('/properties/property-alice')
      .set('authorization', `Bearer ${token}`)
      .send({ title: 'Unauthorized mutation' })
      .expect(404);

    expect(JSON.stringify(response.body)).not.toContain('Synthetic Alice Apartment');
    expect(repository.getProperty('property-alice')).toEqual(before);
    expect(securityEvents.list()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          event: 'authorization_denied',
          actor_id: 'user-bob',
          resource_type: 'property',
          resource_id: 'property-alice',
          action: 'update',
          result: 'denied',
        }),
      ]),
    );
  });

  it('rejects mass assignment before mutation', async () => {
    const token = await login('alice@example.test', 'Alice-Local-Only!42');
    const before = repository.getProperty('property-alice');

    await request(app.getHttpServer())
      .patch('/properties/property-alice')
      .set('authorization', `Bearer ${token}`)
      .send({ title: 'Allowed title', ownerId: 'user-bob', role: 'admin', isVerified: true })
      .expect(400);

    expect(repository.getProperty('property-alice')).toEqual(before);
  });

  it('denies and audits the admin function for an ordinary user', async () => {
    const token = await login('bob@example.test', 'Bob-Local-Only!42');

    await request(app.getHttpServer())
      .get('/admin/audit-events')
      .set('authorization', `Bearer ${token}`)
      .expect(403);

    expect(securityEvents.list()).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          event: 'authorization_denied',
          actor_id: 'user-bob',
          resource_type: 'admin_function',
          result: 'denied',
        }),
      ]),
    );
  });
});
