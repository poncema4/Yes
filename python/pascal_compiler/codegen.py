"""
Alpha AXP Assembly Code Generator for Pascal → Alpha Compiler.

Emits GNU assembler syntax (.s file) targeting the DEC Alpha AXP ISA.

Alpha AXP key facts:
  - 32 × 64-bit integer registers (R0–R31); R31 = zero (hardwired)
  - 32 × 64-bit floating-point registers (F0–F31); F31 = zero
  - Fixed 32-bit instruction encoding
  - RISC: load/store architecture, no condition codes
  - Calling convention:
      R0       = integer return value
      R16–R21  = first 6 integer arguments
      R26      = return address (RA)
      R27      = procedure value (PV) / scratch
      R29      = global pointer (GP)
      R30      = stack pointer (SP)
      R15      = frame pointer (FP) [by convention]
      R2–R8    = callee-saved temporaries
      R9–R14   = callee-saved
  - Arithmetic: ADDQ (64-bit add), SUBQ, MULQ, S4ADDQ (shift-add)
  - Comparisons write result into a register (CMPEQ, CMPLT, CMPLE, etc.)
  - Branches: BEQ/BNE/BLT/BLE/BGT/BGE Rn, label
  - No byte/word loads on early Alpha (we use LDQ/STQ everywhere = 64-bit)
"""

from typing import List, Optional, Dict
from ast_nodes import *
from semantic import (Scope, Symbol, SemanticAnalyser,
                      IntType, RealType, BoolType, CharType, StringType,
                      ArrayPType, ast_type_to_pascal_type)

class CodeGenError(Exception):
    pass

# ── Alpha register names ──────────────────────────────────────────────────────

class Reg:
    V0   = 'v0'    # R0  – return value
    T0   = 't0'    # R1
    T1   = 't1'    # R2
    T2   = 't2'    # R3
    T3   = 't3'    # R4
    T4   = 't4'    # R5
    T5   = 't5'    # R6
    T6   = 't6'    # R7
    T7   = 't7'    # R8
    S0   = 's0'    # R9  – callee-saved
    S1   = 's1'    # R10
    S2   = 's2'    # R11
    S3   = 's3'    # R12
    S4   = 's4'    # R13
    S5   = 's5'    # R14
    FP   = 'fp'    # R15 – frame pointer
    A0   = 'a0'    # R16 – arg0
    A1   = 'a1'    # R17
    A2   = 'a2'    # R18
    A3   = 'a3'    # R19
    A4   = 'a4'    # R20
    A5   = 'a5'    # R21
    RA   = 'ra'    # R26 – return address
    PV   = 'pv'    # R27 – procedure value / scratch
    GP   = 'gp'    # R29 – global pointer
    SP   = 'sp'    # R30 – stack pointer
    ZERO = 'zero'  # R31 – hardwired zero

ARG_REGS = [Reg.A0, Reg.A1, Reg.A2, Reg.A3, Reg.A4, Reg.A5]

# Caller-saved scratch registers (t0–t7)
SCRATCH = [Reg.T0, Reg.T1, Reg.T2, Reg.T3, Reg.T4, Reg.T5, Reg.T6, Reg.T7]

class AlphaCodeGen:
    def __init__(self, scopes: Dict[str, Scope]):
        self.scopes = scopes
        self.global_scope: Scope = scopes['_global']
        self.lines: List[str] = []
        self._label_counter = 0
        self._string_literals: List[tuple] = []  # (label, value)
        self._global_vars: List[tuple] = []       # (name, size)
        self._current_scope: Optional[Scope] = None
        self._current_proc_name: str = '_main'
        self._scratch_idx = 0  # round-robin scratch register

    # ── Emit helpers ──────────────────────────────────────────────────────

    def emit(self, line: str = ''):
        self.lines.append(line)

    def emit_label(self, label: str):
        self.lines.append(f'{label}:')

    def emit_instr(self, mnemonic: str, *args):
        operands = ', '.join(str(a) for a in args)
        self.lines.append(f'\t{mnemonic}\t{operands}' if operands else f'\t{mnemonic}')

    def emit_comment(self, comment: str):
        self.lines.append(f'\t# {comment}')

    def new_label(self, prefix='L') -> str:
        self._label_counter += 1
        return f'{prefix}{self._label_counter}'

    def alloc_scratch(self) -> str:
        r = SCRATCH[self._scratch_idx % len(SCRATCH)]
        self._scratch_idx += 1
        return r

    def reset_scratch(self):
        self._scratch_idx = 0

    # ── Load integer constant into register ───────────────────────────────

    def load_const(self, reg: str, value: int):
        """Load a 64-bit integer constant into reg."""
        if -32768 <= value <= 32767:
            # LDA Rn, value(zero) — loads small immediate
            self.emit_instr('lda', reg, f'{value}({Reg.ZERO})')
        else:
            # LDAH + LDA for larger values
            hi = (value >> 16) & 0xFFFF
            lo = value & 0xFFFF
            if lo >= 0x8000:
                hi += 1   # sign-extension correction
            self.emit_instr('ldah', reg, f'{hi}({Reg.ZERO})')
            if lo:
                self.emit_instr('lda', reg, f'{lo}({reg})')

    # ── Variable address / load / store ───────────────────────────────────

    def _resolve_symbol(self, name: str) -> Symbol:
        sym = self._current_scope.lookup(name)
        if not sym:
            raise CodeGenError(f"Undefined: '{name}'")
        return sym

    def load_var(self, name: str, dest_reg: str):
        """Load a variable's value into dest_reg."""
        sym = self._resolve_symbol(name)
        if sym.is_global:
            # Global: load address from .data section
            self.emit_instr('ldq', dest_reg, f'_var_{name.lower()}')
        else:
            # Local/param: FP-relative
            self.emit_instr('ldq', dest_reg, f'{sym.offset}({Reg.FP})')

    def store_var(self, name: str, src_reg: str):
        """Store src_reg into a variable."""
        sym = self._resolve_symbol(name)
        if sym.is_global:
            tmp = Reg.PV
            self.emit_instr('lda', tmp, f'_var_{name.lower()}')
            self.emit_instr('stq', src_reg, f'0({tmp})')
        else:
            self.emit_instr('stq', src_reg, f'{sym.offset}({Reg.FP})')

    # ── Expression code gen → value in returned register ─────────────────

    def gen_expr(self, expr: Expr, dest: str) -> str:
        """
        Generate code to evaluate expr, placing result in dest.
        Returns the register actually used (may differ for simple loads).
        """
        if isinstance(expr, IntLit):
            self.load_const(dest, expr.value)
            return dest

        elif isinstance(expr, BoolLit):
            self.load_const(dest, 1 if expr.value else 0)
            return dest

        elif isinstance(expr, RealLit):
            # Treat as integer approximation for simplicity
            self.load_const(dest, int(expr.value))
            return dest

        elif isinstance(expr, StrLit):
            lbl = self.new_label('STR')
            self._string_literals.append((lbl, expr.value))
            self.emit_instr('lda', dest, f'{lbl}')
            return dest

        elif isinstance(expr, Var):
            self.load_var(expr.name, dest)
            return dest

        elif isinstance(expr, ArrayAccess):
            arr_sym = self._resolve_symbol(expr.array.name)
            # Compute base address
            base = self.alloc_scratch()
            if arr_sym.is_global:
                self.emit_instr('lda', base, f'_var_{expr.array.name.lower()}')
            else:
                self.emit_instr('lda', base, f'{arr_sym.offset}({Reg.FP})')

            # Compute index, subtract lower bound
            idx = self.alloc_scratch()
            self.gen_expr(expr.index, idx)
            if isinstance(arr_sym.type_, ArrayPType) and arr_sym.type_.low != 0:
                tmp = self.alloc_scratch()
                self.load_const(tmp, arr_sym.type_.low)
                self.emit_instr('subq', idx, tmp, idx)

            # Multiply by element size (8) using S8ADDQ
            self.emit_instr('s8addq', idx, base, base)  # base = idx*8 + base
            self.emit_instr('ldq', dest, f'0({base})')
            return dest

        elif isinstance(expr, UnaryOp):
            r = self.alloc_scratch()
            self.gen_expr(expr.operand, r)
            if expr.op == '-':
                self.emit_instr('subq', Reg.ZERO, r, dest)
            elif expr.op == 'not':
                # Boolean NOT: XOR with 1
                self.emit_instr('xor', r, '1', dest)
            return dest

        elif isinstance(expr, BinOp):
            return self._gen_binop(expr, dest)

        elif isinstance(expr, FuncCall):
            return self._gen_func_call(expr, dest)

        else:
            raise CodeGenError(f"Unknown expr: {type(expr)}")

    def _gen_binop(self, expr: BinOp, dest: str) -> str:
        left_reg = self.alloc_scratch()
        right_reg = self.alloc_scratch()
        self.gen_expr(expr.left, left_reg)
        self.gen_expr(expr.right, right_reg)

        op = expr.op

        # Arithmetic
        if op == '+':
            self.emit_instr('addq', left_reg, right_reg, dest)
        elif op == '-':
            self.emit_instr('subq', left_reg, right_reg, dest)
        elif op == '*':
            self.emit_instr('mulq', left_reg, right_reg, dest)
        elif op in ('/', 'div'):
            # Alpha has no integer divide instruction!
            # We call a helper __divq or use the PALcode
            # For simplicity, call our runtime helper
            self.emit_instr('mov', left_reg, Reg.A0)
            self.emit_instr('mov', right_reg, Reg.A1)
            self.emit_instr('bsr', Reg.RA, '__divq')
            self.emit_instr('mov', Reg.V0, dest)
        elif op == 'mod':
            self.emit_instr('mov', left_reg, Reg.A0)
            self.emit_instr('mov', right_reg, Reg.A1)
            self.emit_instr('bsr', Reg.RA, '__modq')
            self.emit_instr('mov', Reg.V0, dest)

        # Logical
        elif op == 'and':
            self.emit_instr('and', left_reg, right_reg, dest)
        elif op == 'or':
            self.emit_instr('or', left_reg, right_reg, dest)

        # Comparisons — result is 0 or 1 in dest
        elif op == '=':
            self.emit_instr('cmpeq', left_reg, right_reg, dest)
        elif op == '<>':
            self.emit_instr('cmpeq', left_reg, right_reg, dest)
            self.emit_instr('xor', dest, '1', dest)
        elif op == '<':
            self.emit_instr('cmplt', left_reg, right_reg, dest)
        elif op == '<=':
            self.emit_instr('cmple', left_reg, right_reg, dest)
        elif op == '>':
            self.emit_instr('cmplt', right_reg, left_reg, dest)   # swap
        elif op == '>=':
            self.emit_instr('cmple', right_reg, left_reg, dest)   # swap
        else:
            raise CodeGenError(f"Unknown binary op: {op}")

        return dest

    def _gen_func_call(self, expr: FuncCall, dest: str) -> str:
        """Generate a function call, result in dest."""
        # Pass args in A0..A5
        for i, arg in enumerate(expr.args[:6]):
            self.gen_expr(arg, ARG_REGS[i])
        self.emit_instr('bsr', Reg.RA, expr.name.lower())
        if dest != Reg.V0:
            self.emit_instr('mov', Reg.V0, dest)
        return dest

    # ── Statement code gen ────────────────────────────────────────────────

    def gen_stmt(self, stmt: Stmt):
        self.reset_scratch()

        if isinstance(stmt, EmptyStmt):
            pass

        elif isinstance(stmt, Block):
            for s in stmt.stmts:
                self.gen_stmt(s)

        elif isinstance(stmt, Assign):
            self.emit_comment(f'assignment')
            dest = Reg.T0
            self.gen_expr(stmt.value, dest)
            if isinstance(stmt.target, Var):
                self.store_var(stmt.target.name, dest)
            elif isinstance(stmt.target, ArrayAccess):
                arr_sym = self._resolve_symbol(stmt.target.array.name)
                base = Reg.T1
                if arr_sym.is_global:
                    self.emit_instr('lda', base, f'_var_{stmt.target.array.name.lower()}')
                else:
                    self.emit_instr('lda', base, f'{arr_sym.offset}({Reg.FP})')
                idx = Reg.T2
                self.gen_expr(stmt.target.index, idx)
                if isinstance(arr_sym.type_, ArrayPType) and arr_sym.type_.low != 0:
                    tmp = Reg.T3
                    self.load_const(tmp, arr_sym.type_.low)
                    self.emit_instr('subq', idx, tmp, idx)
                self.emit_instr('s8addq', idx, base, base)
                self.emit_instr('stq', dest, f'0({base})')

        elif isinstance(stmt, IfStmt):
            self._gen_if(stmt)

        elif isinstance(stmt, WhileStmt):
            self._gen_while(stmt)

        elif isinstance(stmt, ForStmt):
            self._gen_for(stmt)

        elif isinstance(stmt, RepeatStmt):
            self._gen_repeat(stmt)

        elif isinstance(stmt, WritelnStmt):
            self._gen_writeln(stmt)

        elif isinstance(stmt, ReadlnStmt):
            self._gen_readln(stmt)

        elif isinstance(stmt, ProcCall):
            self._gen_proc_call(stmt)

    def _gen_if(self, stmt: IfStmt):
        else_lbl = self.new_label('ELSE')
        end_lbl  = self.new_label('ENDIF')
        self.emit_comment('if statement')
        cond_reg = Reg.T0
        self.gen_expr(stmt.condition, cond_reg)
        # BEQ cond, else_label  (branch if condition == 0, i.e. false)
        self.emit_instr('beq', cond_reg, else_lbl)
        self.gen_stmt(stmt.then_branch)
        if stmt.else_branch:
            self.emit_instr('br', Reg.ZERO, end_lbl)
            self.emit_label(else_lbl)
            self.gen_stmt(stmt.else_branch)
            self.emit_label(end_lbl)
        else:
            self.emit_label(else_lbl)

    def _gen_while(self, stmt: WhileStmt):
        loop_lbl = self.new_label('WHILE')
        end_lbl  = self.new_label('ENDWHILE')
        self.emit_comment('while loop')
        self.emit_label(loop_lbl)
        cond_reg = Reg.T0
        self.gen_expr(stmt.condition, cond_reg)
        self.emit_instr('beq', cond_reg, end_lbl)
        self.gen_stmt(stmt.body)
        self.emit_instr('br', Reg.ZERO, loop_lbl)
        self.emit_label(end_lbl)

    def _gen_for(self, stmt: ForStmt):
        """
        FOR var := start TO stop DO body
        Translated to:
          var := start
          LOOP: if var > stop then exit
                body
                var := var ± 1
                goto LOOP
        """
        loop_lbl = self.new_label('FOR')
        end_lbl  = self.new_label('ENDFOR')
        self.emit_comment(f'for {stmt.var}')
        # Initialise loop variable
        r_init = Reg.T0
        self.gen_expr(stmt.start, r_init)
        self.store_var(stmt.var, r_init)
        self.emit_label(loop_lbl)
        # Check condition
        r_var   = Reg.T0
        r_limit = Reg.T1
        r_cmp   = Reg.T2
        self.load_var(stmt.var, r_var)
        self.gen_expr(stmt.stop, r_limit)
        if stmt.downto:
            self.emit_instr('cmplt', r_var, r_limit, r_cmp)
        else:
            self.emit_instr('cmplt', r_limit, r_var, r_cmp)   # stop < var
        self.emit_instr('bne', r_cmp, end_lbl)
        # Body
        self.gen_stmt(stmt.body)
        # Increment / decrement
        self.load_var(stmt.var, r_var)
        if stmt.downto:
            self.emit_instr('subq', r_var, '1', r_var)
        else:
            self.emit_instr('addq', r_var, '1', r_var)
        self.store_var(stmt.var, r_var)
        self.emit_instr('br', Reg.ZERO, loop_lbl)
        self.emit_label(end_lbl)

    def _gen_repeat(self, stmt: RepeatStmt):
        loop_lbl = self.new_label('REPEAT')
        self.emit_comment('repeat..until')
        self.emit_label(loop_lbl)
        for s in stmt.body:
            self.gen_stmt(s)
        cond_reg = Reg.T0
        self.gen_expr(stmt.condition, cond_reg)
        self.emit_instr('beq', cond_reg, loop_lbl)   # loop if cond is false

    def _gen_writeln(self, stmt: WritelnStmt):
        """
        Call C runtime printf/putchar via our __print_* helpers.
        Each argument type dispatches to a different helper.
        """
        self.emit_comment('writeln')
        for arg in stmt.args:
            if isinstance(arg, StrLit):
                lbl = self.new_label('STR')
                self._string_literals.append((lbl, arg.value))
                self.emit_instr('lda', Reg.A0, lbl)
                self.emit_instr('bsr', Reg.RA, '__print_str')
            else:
                # Evaluate into A0, call __print_int
                self.gen_expr(arg, Reg.A0)
                self.emit_instr('bsr', Reg.RA, '__print_int')
        if stmt.newline:
            self.emit_instr('bsr', Reg.RA, '__print_newline')

    def _gen_readln(self, stmt: ReadlnStmt):
        self.emit_comment('readln')
        for arg in stmt.args:
            self.emit_instr('bsr', Reg.RA, '__read_int')
            if isinstance(arg, Var):
                self.store_var(arg.name, Reg.V0)

    def _gen_proc_call(self, stmt: ProcCall):
        self.emit_comment(f'call {stmt.name}')
        for i, arg in enumerate(stmt.args[:6]):
            self.gen_expr(arg, ARG_REGS[i])
        self.emit_instr('bsr', Reg.RA, stmt.name.lower())

    # ── Procedure / function prologue and epilogue ────────────────────────

    def gen_proc(self, proc: ProcDecl):
        scope = self.scopes.get(proc.name.lower())
        if not scope:
            raise CodeGenError(f"No scope for {proc.name}")

        outer_scope = self._current_scope
        self._current_scope = scope
        outer_name  = self._current_proc_name
        self._current_proc_name = proc.name.lower()

        frame = max(scope.frame_size + 16, 32)   # at least 32 bytes
        frame = (frame + 15) & ~15               # 16-byte align

        self.emit()
        self.emit_comment(f'─── Procedure: {proc.name} ───')
        self.emit_label(proc.name.lower())
        # Prologue
        self.emit_comment('prologue: save RA, FP; set new FP')
        self.emit_instr('lda', Reg.SP, f'-{frame}({Reg.SP})')
        self.emit_instr('stq', Reg.RA, f'{frame - 8}({Reg.SP})')
        self.emit_instr('stq', Reg.FP, f'{frame - 16}({Reg.SP})')
        self.emit_instr('mov', Reg.SP, Reg.FP)

        # Nested procedures first
        for nested in proc.nested:
            self.gen_proc(nested)

        # Body
        for s in proc.body.stmts:
            self.gen_stmt(s)

        # Function return value: load var with same name as function
        if proc.return_type:
            self.load_var(proc.name, Reg.V0)

        # Epilogue
        self.emit_comment('epilogue: restore RA, FP; return')
        self.emit_instr('mov', Reg.FP, Reg.SP)
        self.emit_instr('ldq', Reg.RA, f'{frame - 8}({Reg.SP})')
        self.emit_instr('ldq', Reg.FP, f'{frame - 16}({Reg.SP})')
        self.emit_instr('lda', Reg.SP, f'{frame}({Reg.SP})')
        self.emit_instr('ret', Reg.ZERO, f'({Reg.RA})', '1')

        self._current_scope = outer_scope
        self._current_proc_name = outer_name

    # ── Main program ──────────────────────────────────────────────────────

    def gen_program(self, prog: Program) -> str:
        self._current_scope = self.global_scope

        # Collect global variable info
        for decl in prog.var_decls:
            pt = ast_type_to_pascal_type(decl.type_)
            size = getattr(pt, 'SIZE', 8)
            for name in decl.names:
                self._global_vars.append((name.lower(), size))

        # Text section header
        self.emit('\t.text')
        self.emit('\t.align 3')
        self.emit()

        # Runtime helpers (called by print/read stubs)
        self._emit_runtime_stubs()

        # Procedures / functions
        for proc in prog.procedures:
            self.gen_proc(proc)

        # Main entry point
        self.emit()
        self.emit_comment('─── Main program entry point ───')
        self.emit('\t.globl\t_start')
        self.emit_label('_start')

        main_frame = 32
        self.emit_instr('lda', Reg.SP, f'-{main_frame}({Reg.SP})')
        self.emit_instr('stq', Reg.RA, f'{main_frame - 8}({Reg.SP})')
        self.emit_instr('stq', Reg.FP, f'{main_frame - 16}({Reg.SP})')
        self.emit_instr('mov', Reg.SP, Reg.FP)

        for s in prog.body.stmts:
            self.gen_stmt(s)

        self.emit_instr('mov', Reg.FP, Reg.SP)
        self.emit_instr('ldq', Reg.RA, f'{main_frame - 8}({Reg.SP})')
        self.emit_instr('ldq', Reg.FP, f'{main_frame - 16}({Reg.SP})')
        self.emit_instr('lda', Reg.SP, f'{main_frame}({Reg.SP})')
        # Exit via PALcode (Tru64 / Linux syscall equivalent)
        self.emit_comment('exit(0) via PALcode')
        self.emit_instr('mov', Reg.ZERO, Reg.A0)
        self.emit_instr('call_pal', '0x0001')   # PAL_halt or exit

        # ── Data section ──────────────────────────────────────────────────
        self.emit()
        self.emit('\t.data')
        self.emit('\t.align 3')

        # Global variable storage
        for name, size in self._global_vars:
            self.emit()
            self.emit_comment(f'global variable: {name} ({size} bytes)')
            self.emit(f'\t.globl\t_var_{name}')
            self.emit(f'_var_{name}:')
            self.emit(f'\t.space\t{size}')

        # String literals
        for lbl, val in self._string_literals:
            escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            self.emit(f'{lbl}:')
            self.emit(f'\t.asciz\t"{escaped}"')

        # Constant string messages used by runtime
        self.emit()
        self.emit('_fmt_int:')
        self.emit('\t.asciz\t"%ld"')
        self.emit('_fmt_int_in:')
        self.emit('\t.asciz\t"%ld"')
        self.emit('_newline:')
        self.emit('\t.asciz\t"\\n"')

        return '\n'.join(self.lines)

    def _emit_runtime_stubs(self):
        """
        Emit Alpha assembly stubs that call C library functions.
        In a real build these would be linked against libc / Tru64's crt0.
        Here we emit them as proper Alpha call stubs.
        """
        self.emit_comment('=== Runtime support stubs ===')
        self.emit()

        # __print_int: print integer in A0
        self.emit_comment('__print_int(A0=value)')
        self.emit_label('__print_int')
        self.emit_instr('lda', Reg.SP, '-16(sp)')
        self.emit_instr('stq', Reg.RA, '8(sp)')
        self.emit_instr('mov', Reg.A0, Reg.A1)          # value → arg1
        self.emit_instr('lda', Reg.A0, '_fmt_int')       # format → arg0
        self.emit_instr('bsr', Reg.RA, 'printf')
        self.emit_instr('ldq', Reg.RA, '8(sp)')
        self.emit_instr('lda', Reg.SP, '16(sp)')
        self.emit_instr('ret', Reg.ZERO, f'({Reg.RA})', '1')
        self.emit()

        # __print_str: print null-terminated string in A0
        self.emit_comment('__print_str(A0=ptr)')
        self.emit_label('__print_str')
        self.emit_instr('lda', Reg.SP, '-16(sp)')
        self.emit_instr('stq', Reg.RA, '8(sp)')
        self.emit_instr('bsr', Reg.RA, 'printf')
        self.emit_instr('ldq', Reg.RA, '8(sp)')
        self.emit_instr('lda', Reg.SP, '16(sp)')
        self.emit_instr('ret', Reg.ZERO, f'({Reg.RA})', '1')
        self.emit()

        # __print_newline: print '\n'
        self.emit_comment('__print_newline()')
        self.emit_label('__print_newline')
        self.emit_instr('lda', Reg.SP, '-16(sp)')
        self.emit_instr('stq', Reg.RA, '8(sp)')
        self.emit_instr('lda', Reg.A0, '_newline')
        self.emit_instr('bsr', Reg.RA, 'printf')
        self.emit_instr('ldq', Reg.RA, '8(sp)')
        self.emit_instr('lda', Reg.SP, '16(sp)')
        self.emit_instr('ret', Reg.ZERO, f'({Reg.RA})', '1')
        self.emit()

        # __read_int: read integer → V0
        self.emit_comment('__read_int() -> V0')
        self.emit_label('__read_int')
        self.emit_instr('lda', Reg.SP, '-32(sp)')
        self.emit_instr('stq', Reg.RA, '24(sp)')
        self.emit_instr('lda', Reg.A0, '_fmt_int_in')
        self.emit_instr('lda', Reg.A1, '16(sp)')          # buffer on stack
        self.emit_instr('bsr', Reg.RA, 'scanf')
        self.emit_instr('ldq', Reg.V0, '16(sp)')
        self.emit_instr('ldq', Reg.RA, '24(sp)')
        self.emit_instr('lda', Reg.SP, '32(sp)')
        self.emit_instr('ret', Reg.ZERO, f'({Reg.RA})', '1')
        self.emit()

        # __divq: integer divide A0 / A1 → V0  (software routine)
        self.emit_comment('__divq(A0, A1) -> V0  (A0 div A1)')
        self.emit_label('__divq')
        # Simple non-restoring binary division (no hardware divide on Alpha)
        # For correctness in our compiler we use a loop; real compilers use
        # strength reduction and the __divq from the OS PALcode library.
        self.emit_instr('lda', Reg.SP, '-32(sp)')
        self.emit_instr('stq', Reg.RA, '24(sp)')
        # Call C library __divl via OS (simplified)
        self.emit_instr('bsr', Reg.RA, '__os_divq')
        self.emit_instr('ldq', Reg.RA, '24(sp)')
        self.emit_instr('lda', Reg.SP, '32(sp)')
        self.emit_instr('ret', Reg.ZERO, f'({Reg.RA})', '1')
        self.emit()

        # __modq
        self.emit_comment('__modq(A0, A1) -> V0  (A0 mod A1)')
        self.emit_label('__modq')
        self.emit_instr('lda', Reg.SP, '-32(sp)')
        self.emit_instr('stq', Reg.RA, '24(sp)')
        self.emit_instr('bsr', Reg.RA, '__os_modq')
        self.emit_instr('ldq', Reg.RA, '24(sp)')
        self.emit_instr('lda', Reg.SP, '32(sp)')
        self.emit_instr('ret', Reg.ZERO, f'({Reg.RA})', '1')
        self.emit()
        self.emit_comment('=== End runtime stubs ===')
        self.emit()