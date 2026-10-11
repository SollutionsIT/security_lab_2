declare class ValidationPipe {
  constructor(options: object);
}

// ruleid: company.validation-pipe-must-forbid-extra-fields
new ValidationPipe({ whitelist: true, transform: true });

// ok: company.validation-pipe-must-forbid-extra-fields
new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true });
