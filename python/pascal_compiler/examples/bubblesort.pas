{ ═══════════════════════════════════════════════════
  Example 4: Bubble Sort on an array
  ═══════════════════════════════════════════════════ }
program BubbleSort;
var
  arr : array[1..10] of integer;
  i, j, tmp : integer;
  n : integer;

begin
  n := 10;
  { Initialise with values in reverse order }
  arr[1]  := 64;
  arr[2]  := 34;
  arr[3]  := 25;
  arr[4]  := 12;
  arr[5]  := 22;
  arr[6]  := 11;
  arr[7]  := 90;
  arr[8]  := 3;
  arr[9]  := 55;
  arr[10] := 77;

  { Bubble sort }
  for i := 1 to n - 1 do
  begin
    for j := 1 to n - i do
    begin
      if arr[j] > arr[j + 1] then
      begin
        tmp        := arr[j];
        arr[j]     := arr[j + 1];
        arr[j + 1] := tmp
      end
    end
  end;

  writeln('Sorted array:');
  for i := 1 to n do
    write(arr[i]);
  writeln('')
end.
