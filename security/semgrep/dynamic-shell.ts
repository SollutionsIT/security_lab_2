declare function exec(command: string): void;

function positive(userInput: string) {
  // ruleid: company.no-dynamic-shell-exec
  exec(userInput);
}

function negative() {
  // ok: company.no-dynamic-shell-exec
  exec('/usr/bin/true');
}

void positive;
void negative;
