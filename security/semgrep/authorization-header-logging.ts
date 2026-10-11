function positive(request: { headers: { authorization: string } }) {
  // ruleid: company.no-authorization-header-logging
  console.log(request.headers.authorization);
}

function negative() {
  // ok: company.no-authorization-header-logging
  console.log({ event: 'authentication_failed', credential: '[REDACTED]' });
}

void positive;
void negative;
