"""
AST node definitions for Pascal → Alpha Compiler.
Every Pascal construct becomes one of these nodes.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any

# ── Types ────────────────────────────────────────────────────────────────────

@dataclass
class TypeNode:
    pass

@dataclass
class SimpleType(TypeNode):
    name: str          # 'integer', 'real', 'boolean', 'char', 'string'

@dataclass
class ArrayType(TypeNode):
    low: int
    high: int
    element_type: TypeNode

@dataclass
class RecordType(TypeNode):
    fields: List[tuple]   # [(name, TypeNode), ...]

# ── Expressions ──────────────────────────────────────────────────────────────

@dataclass
class Expr:
    pass

@dataclass
class IntLit(Expr):
    value: int

@dataclass
class RealLit(Expr):
    value: float

@dataclass
class StrLit(Expr):
    value: str

@dataclass
class BoolLit(Expr):
    value: bool

@dataclass
class Var(Expr):
    name: str

@dataclass
class ArrayAccess(Expr):
    array: Expr
    index: Expr

@dataclass
class BinOp(Expr):
    op: str          # '+', '-', '*', '/', 'div', 'mod', 'and', 'or',
                     # '=', '<>', '<', '<=', '>', '>='
    left: Expr
    right: Expr

@dataclass
class UnaryOp(Expr):
    op: str          # '-', 'not'
    operand: Expr

@dataclass
class FuncCall(Expr):
    name: str
    args: List[Expr]

# ── Statements ───────────────────────────────────────────────────────────────

@dataclass
class Stmt:
    pass

@dataclass
class Assign(Stmt):
    target: Expr     # Var or ArrayAccess
    value: Expr

@dataclass
class ProcCall(Stmt):
    name: str
    args: List[Expr]

@dataclass
class WritelnStmt(Stmt):
    args: List[Expr]
    newline: bool = True   # False → write, True → writeln

@dataclass
class ReadlnStmt(Stmt):
    args: List[Expr]

@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt]

@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: Stmt

@dataclass
class ForStmt(Stmt):
    var: str
    start: Expr
    stop: Expr
    downto: bool
    body: Stmt

@dataclass
class RepeatStmt(Stmt):
    body: List[Stmt]
    condition: Expr

@dataclass
class Block(Stmt):
    stmts: List[Stmt]

@dataclass
class EmptyStmt(Stmt):
    pass

# ── Declarations ─────────────────────────────────────────────────────────────

@dataclass
class VarDecl:
    names: List[str]
    type_: TypeNode

@dataclass
class ParamDecl:
    names: List[str]
    type_: TypeNode
    by_ref: bool = False   # True → VAR parameter

@dataclass
class ProcDecl:
    name: str
    params: List[ParamDecl]
    return_type: Optional[TypeNode]   # None → procedure, set → function
    var_decls: List[VarDecl]
    body: Block
    nested: List['ProcDecl'] = field(default_factory=list)

@dataclass
class Program:
    name: str
    var_decls: List[VarDecl]
    procedures: List[ProcDecl]
    body: Block