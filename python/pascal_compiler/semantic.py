"""
Symbol table and semantic analysis for Pascal → Alpha Compiler.
Resolves names, checks types, computes stack frame layouts.
"""

from typing import Dict, List, Optional, Tuple
from ast_nodes import *
from dataclasses import dataclass, field


# ── Type system ───────────────────────────────────────────────────────────────

class PascalType:
    pass

class IntType(PascalType):
    SIZE = 8  # 64-bit on Alpha
    def __repr__(self): return 'integer'

class RealType(PascalType):
    SIZE = 8
    def __repr__(self): return 'real'

class BoolType(PascalType):
    SIZE = 8
    def __repr__(self): return 'boolean'

class CharType(PascalType):
    SIZE = 8
    def __repr__(self): return 'char'

class StringType(PascalType):
    SIZE = 256   # fixed-size string buffer
    def __repr__(self): return 'string'

@dataclass
class ArrayPType(PascalType):
    low: int
    high: int
    elem: PascalType
    def __repr__(self):
        return f'array[{self.low}..{self.high}] of {self.elem}'
    @property
    def SIZE(self):
        return (self.high - self.low + 1) * self.elem.SIZE

@dataclass
class ProcType(PascalType):
    params: list
    return_type: Optional[PascalType]

INT_T  = IntType()
REAL_T = RealType()
BOOL_T = BoolType()
CHAR_T = CharType()
STR_T  = StringType()

TYPE_MAP = {
    'integer': INT_T,
    'real':    REAL_T,
    'boolean': BOOL_T,
    'char':    CHAR_T,
    'string':  STR_T,
}

def ast_type_to_pascal_type(t: TypeNode) -> PascalType:
    if isinstance(t, SimpleType):
        pt = TYPE_MAP.get(t.name.lower())
        if pt is None:
            raise SemanticError(f"Unknown type: {t.name}")
        return pt
    elif isinstance(t, ArrayType):
        elem = ast_type_to_pascal_type(t.element_type)
        return ArrayPType(low=t.low, high=t.high, elem=elem)
    raise SemanticError(f"Unsupported type node: {t}")


# ── Symbol table ──────────────────────────────────────────────────────────────

@dataclass
class Symbol:
    name: str
    type_: PascalType
    offset: int          # byte offset from frame pointer (negative = local)
    is_param: bool = False
    by_ref: bool = False
    is_global: bool = False

class Scope:
    def __init__(self, name: str, parent: Optional['Scope'] = None):
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.next_offset = -8     # locals grow downward from FP
        self.param_offset = 16    # params above FP (16 = saved RA + FP)
        self.frame_size = 0

    def declare(self, name: str, type_: PascalType, is_param=False,
                by_ref=False, is_global=False) -> Symbol:
        if name.lower() in self.symbols:
            raise SemanticError(f"Duplicate declaration: '{name}'")
        size = getattr(type_, 'SIZE', 8)
        if is_global:
            sym = Symbol(name.lower(), type_, 0, is_global=True)
        elif is_param:
            sym = Symbol(name.lower(), type_, self.param_offset,
                         is_param=True, by_ref=by_ref)
            self.param_offset += 8
        else:
            sym = Symbol(name.lower(), type_, self.next_offset)
            self.next_offset -= size
            self.frame_size += size
        self.symbols[name.lower()] = sym
        return sym

    def lookup(self, name: str) -> Optional[Symbol]:
        sym = self.symbols.get(name.lower())
        if sym:
            return sym
        if self.parent:
            return self.parent.lookup(name)
        return None

class SemanticError(Exception):
    pass

# ── Semantic analyser ─────────────────────────────────────────────────────────

class SemanticAnalyser:
    """
    Walk the AST:
      1. Build nested Scope objects
      2. Assign stack offsets to every variable
      3. Type-check expressions (basic)
    Returns the global Scope + a mapping proc_name → Scope.
    """

    def __init__(self):
        self.global_scope = Scope('_global')
        self.scopes: Dict[str, Scope] = {'_global': self.global_scope}
        self.current_scope: Scope = self.global_scope

    def analyse(self, prog: Program) -> Scope:
        # Global variable declarations
        for decl in prog.var_decls:
            pt = ast_type_to_pascal_type(decl.type_)
            for name in decl.names:
                self.global_scope.declare(name, pt, is_global=True)

        # Procedure / function declarations
        for proc in prog.procedures:
            self._analyse_proc(proc)

        # Main body
        self._analyse_block(prog.body, self.global_scope)
        return self.global_scope

    def _analyse_proc(self, proc: ProcDecl):
        scope = Scope(proc.name, parent=self.current_scope)
        self.scopes[proc.name.lower()] = scope

        # Parameters
        for param in proc.params:
            pt = ast_type_to_pascal_type(param.type_)
            for name in param.names:
                scope.declare(name, pt, is_param=True, by_ref=param.by_ref)

        # Return value slot (function only)
        if proc.return_type:
            rt = ast_type_to_pascal_type(proc.return_type)
            scope.declare(proc.name, rt)   # return value via proc name

        # Local variables
        for decl in proc.var_decls:
            pt = ast_type_to_pascal_type(decl.type_)
            for name in decl.names:
                scope.declare(name, pt)

        # Nested procedures
        outer = self.current_scope
        self.current_scope = scope
        for nested in proc.nested:
            self._analyse_proc(nested)
        self._analyse_block(proc.body, scope)
        self.current_scope = outer

        # Align frame size to 16-byte boundary
        scope.frame_size = (scope.frame_size + 15) & ~15

    def _analyse_block(self, block: Block, scope: Scope):
        for stmt in block.stmts:
            self._analyse_stmt(stmt, scope)

    def _analyse_stmt(self, stmt: Stmt, scope: Scope):
        if isinstance(stmt, Block):
            self._analyse_block(stmt, scope)
        elif isinstance(stmt, Assign):
            self._analyse_expr(stmt.value, scope)
        elif isinstance(stmt, IfStmt):
            self._analyse_expr(stmt.condition, scope)
            self._analyse_stmt(stmt.then_branch, scope)
            if stmt.else_branch:
                self._analyse_stmt(stmt.else_branch, scope)
        elif isinstance(stmt, WhileStmt):
            self._analyse_expr(stmt.condition, scope)
            self._analyse_stmt(stmt.body, scope)
        elif isinstance(stmt, ForStmt):
            self._analyse_expr(stmt.start, scope)
            self._analyse_expr(stmt.stop, scope)
            self._analyse_stmt(stmt.body, scope)
        elif isinstance(stmt, RepeatStmt):
            for s in stmt.body:
                self._analyse_stmt(s, scope)
            self._analyse_expr(stmt.condition, scope)
        elif isinstance(stmt, WritelnStmt):
            for a in stmt.args:
                self._analyse_expr(a, scope)
        elif isinstance(stmt, ReadlnStmt):
            pass
        elif isinstance(stmt, (ProcCall,)):
            for a in stmt.args:
                self._analyse_expr(a, scope)

    def _analyse_expr(self, expr: Expr, scope: Scope):
        if isinstance(expr, Var):
            sym = scope.lookup(expr.name)
            if not sym:
                raise SemanticError(f"Undefined variable: '{expr.name}'")
        elif isinstance(expr, BinOp):
            self._analyse_expr(expr.left, scope)
            self._analyse_expr(expr.right, scope)
        elif isinstance(expr, UnaryOp):
            self._analyse_expr(expr.operand, scope)
        elif isinstance(expr, FuncCall):
            for a in expr.args:
                self._analyse_expr(a, scope)
        elif isinstance(expr, ArrayAccess):
            self._analyse_expr(expr.array, scope)
            self._analyse_expr(expr.index, scope)