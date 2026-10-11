import { BadRequestException, Injectable } from '@nestjs/common';
import { XMLParser, XMLValidator } from 'fast-xml-parser';
import { SecurityEventsService } from '../../security/security-events.service';

export const XML_LIMITS = Object.freeze({
  maxBytes: 32_768,
  maxDepth: 8,
  maxNodes: 128,
});

export interface XmlImportSummary {
  readonly accepted: true;
  readonly rootElement: string;
  readonly nodeCount: number;
  readonly maxDepth: number;
}

interface XmlShape {
  readonly rootElement: string;
  readonly nodeCount: number;
  readonly maxDepth: number;
}

const FORBIDDEN_DECLARATION = /<!\s*(?:DOCTYPE|ENTITY)\b/i;
const ENTITY_REFERENCE = /&(?:#\d+|#x[\da-f]+|[a-z_][\w.:-]*);/i;
const TAG_TOKEN = /<[^>]*>/g;

function inspectShape(xml: string): XmlShape {
  let depth = 0;
  let maxDepth = 0;
  let nodeCount = 0;
  let rootElement = '';

  for (const match of xml.matchAll(TAG_TOKEN)) {
    const token = match[0];
    if (
      token.startsWith('<?') ||
      token.startsWith('<!--') ||
      token.startsWith('<![CDATA[')
    ) {
      continue;
    }
    if (token.startsWith('</')) {
      depth -= 1;
      if (depth < 0) {
        throw new BadRequestException('XML element structure is invalid');
      }
      continue;
    }
    if (token.startsWith('<!')) {
      throw new BadRequestException('XML declarations are not allowed');
    }

    const name = /^<\s*([A-Za-z_][\w.:-]*)/.exec(token)?.[1];
    if (!name) {
      throw new BadRequestException('XML element name is invalid');
    }
    nodeCount += 1;
    if (nodeCount > XML_LIMITS.maxNodes) {
      throw new BadRequestException('XML node limit exceeded');
    }
    if (!rootElement) {
      rootElement = name;
    }
    if (!/\/\s*>$/.test(token)) {
      depth += 1;
      maxDepth = Math.max(maxDepth, depth);
      if (maxDepth > XML_LIMITS.maxDepth) {
        throw new BadRequestException('XML nesting limit exceeded');
      }
    }
  }

  if (!rootElement || nodeCount === 0 || depth !== 0) {
    throw new BadRequestException('XML document is empty or unbalanced');
  }
  return { rootElement, nodeCount, maxDepth };
}

@Injectable()
export class XmlImportService {
  private readonly parser = new XMLParser({
    ignoreAttributes: false,
    allowBooleanAttributes: false,
    processEntities: false,
    trimValues: true,
    parseTagValue: false,
    parseAttributeValue: false,
  });

  constructor(private readonly securityEvents: SecurityEventsService) {}

  parse(rawXml: string | Buffer, correlationId: string): XmlImportSummary {
    const xml = Buffer.isBuffer(rawXml) ? rawXml.toString('utf8') : rawXml;
    if (typeof xml !== 'string' || xml.trim().length === 0) {
      throw new BadRequestException('A non-empty XML document is required');
    }
    if (Buffer.byteLength(xml, 'utf8') > XML_LIMITS.maxBytes) {
      throw new BadRequestException('XML size limit exceeded');
    }
    if (FORBIDDEN_DECLARATION.test(xml) || ENTITY_REFERENCE.test(xml)) {
      throw new BadRequestException('DTD and entity processing is disabled');
    }

    const shape = inspectShape(xml);
    const validation = XMLValidator.validate(xml, {
      allowBooleanAttributes: false,
    });
    if (validation !== true) {
      throw new BadRequestException('XML document is malformed');
    }

    // fast-xml-parser is a non-networking parser. processEntities=false and the
    // lexical rejection above keep entity expansion outside this trust boundary.
    this.parser.parse(xml);
    this.securityEvents.record({
      event: 'xml_import_accepted',
      resourceType: 'xml_import',
      action: 'parse',
      result: 'accepted',
      correlationId,
      metadata: {
        root_element: shape.rootElement,
        node_count: shape.nodeCount,
        max_depth: shape.maxDepth,
      },
    });
    return { accepted: true, ...shape };
  }
}
