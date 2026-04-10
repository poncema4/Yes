{ ═══════════════════════════════════════════════════
  Example 3: Factorial using a function
  ═══════════════════════════════════════════════════ }
program FactorialDemo;
var
  i, result : integer;

function factorial(n : integer) : integer;
var
  f : integer;
begin
  f := 1;
  while n > 1 do
  begin
    f := f * n;
    n := n - 1
  end;
  factorial := f
end;

begin
  writeln('Factorials 1..10:');
  for i := 1 to 10 do
  begin
    result := factorial(i);
    write(result)
  end;
  writeln('')
end.
