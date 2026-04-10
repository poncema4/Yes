{ ═══════════════════════════════════════════════════
  Example 2: Fibonacci sequence with a loop
  ═══════════════════════════════════════════════════ }
program Fibonacci;
var
  n, a, b, tmp, i : integer;

begin
  n := 15;
  a := 0;
  b := 1;
  writeln('Fibonacci sequence:');
  write(a);
  write(b);
  for i := 2 to n do
  begin
    tmp := a + b;
    a := b;
    b := tmp;
    write(b)
  end;
  writeln('')
end.
