declare function jwtVerify(token: string, key: Uint8Array, options: object): void;

function positive(token: string, key: Uint8Array) {
  // ruleid: company.jwt-verify-must-constrain-algorithm
  jwtVerify(token, key, { issuer: 'example' });
}

function negative(token: string, key: Uint8Array) {
  // ok: company.jwt-verify-must-constrain-algorithm
  jwtVerify(token, key, { issuer: 'example', algorithms: ['HS256'] });
}

void positive;
void negative;
