import { BadRequestException } from '@nestjs/common';
import type { SecurityEventsService } from '../../security/security-events.service';
import { XML_LIMITS, XmlImportService } from './xml-import.service';

describe('XmlImportService', () => {
  const events = { record: jest.fn() } as unknown as SecurityEventsService;
  const service = new XmlImportService(events);

  it('accepts a bounded document without returning parsed content', () => {
    expect(
      service.parse(
        '<properties><property><title>Synthetic</title></property></properties>',
        'correlation-1234',
      ),
    ).toEqual({
      accepted: true,
      rootElement: 'properties',
      nodeCount: 3,
      maxDepth: 3,
    });
  });

  it.each([
    '<!DOCTYPE root [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>',
    '<root>&amp;</root>',
    '<root><child></root>',
  ])('rejects declarations, entities, and malformed XML', (xml) => {
    expect(() => service.parse(xml, 'correlation-1234')).toThrow(
      BadRequestException,
    );
  });

  it('rejects oversized XML before parsing', () => {
    const xml = `<root>${'x'.repeat(XML_LIMITS.maxBytes)}</root>`;
    expect(() => service.parse(xml, 'correlation-1234')).toThrow(
      BadRequestException,
    );
  });

  it('rejects excessive nesting', () => {
    const xml = `${'<n>'.repeat(XML_LIMITS.maxDepth + 1)}${'</n>'.repeat(
      XML_LIMITS.maxDepth + 1,
    )}`;
    expect(() => service.parse(xml, 'correlation-1234')).toThrow(
      BadRequestException,
    );
  });

  it('rejects excessive node counts', () => {
    const xml = `<root>${'<n/>'.repeat(XML_LIMITS.maxNodes)}</root>`;
    expect(() => service.parse(xml, 'correlation-1234')).toThrow(
      BadRequestException,
    );
  });
});
