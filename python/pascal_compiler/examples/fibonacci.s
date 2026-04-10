	.text
	.align 3

	# === Runtime support stubs ===

	# __print_int(A0=value)
__print_int:
	lda	sp, -16(sp)
	stq	ra, 8(sp)
	mov	a0, a1
	lda	a0, _fmt_int
	bsr	ra, printf
	ldq	ra, 8(sp)
	lda	sp, 16(sp)
	ret	zero, (ra), 1

	# __print_str(A0=ptr)
__print_str:
	lda	sp, -16(sp)
	stq	ra, 8(sp)
	bsr	ra, printf
	ldq	ra, 8(sp)
	lda	sp, 16(sp)
	ret	zero, (ra), 1

	# __print_newline()
__print_newline:
	lda	sp, -16(sp)
	stq	ra, 8(sp)
	lda	a0, _newline
	bsr	ra, printf
	ldq	ra, 8(sp)
	lda	sp, 16(sp)
	ret	zero, (ra), 1

	# __read_int() -> V0
__read_int:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	lda	a0, _fmt_int_in
	lda	a1, 16(sp)
	bsr	ra, scanf
	ldq	v0, 16(sp)
	ldq	ra, 24(sp)
	lda	sp, 32(sp)
	ret	zero, (ra), 1

	# __divq(A0, A1) -> V0  (A0 div A1)
__divq:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	bsr	ra, __os_divq
	ldq	ra, 24(sp)
	lda	sp, 32(sp)
	ret	zero, (ra), 1

	# __modq(A0, A1) -> V0  (A0 mod A1)
__modq:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	bsr	ra, __os_modq
	ldq	ra, 24(sp)
	lda	sp, 32(sp)
	ret	zero, (ra), 1

	# === End runtime stubs ===


	# ─── Main program entry point ───
	.globl	_start
_start:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	stq	fp, 16(sp)
	mov	sp, fp
	# assignment
	lda	t0, 15(zero)
	lda	pv, _var_n
	stq	t0, 0(pv)
	# assignment
	lda	t0, 0(zero)
	lda	pv, _var_a
	stq	t0, 0(pv)
	# assignment
	lda	t0, 1(zero)
	lda	pv, _var_b
	stq	t0, 0(pv)
	# writeln
	lda	a0, STR1
	bsr	ra, __print_str
	bsr	ra, __print_newline
	# writeln
	ldq	a0, _var_a
	bsr	ra, __print_int
	# writeln
	ldq	a0, _var_b
	bsr	ra, __print_int
	# for i
	lda	t0, 2(zero)
	lda	pv, _var_i
	stq	t0, 0(pv)
FOR2:
	ldq	t0, _var_i
	ldq	t1, _var_n
	cmplt	t1, t0, t2
	bne	t2, ENDFOR3
	# assignment
	ldq	t0, _var_a
	ldq	t1, _var_b
	addq	t0, t1, t0
	lda	pv, _var_tmp
	stq	t0, 0(pv)
	# assignment
	ldq	t0, _var_b
	lda	pv, _var_a
	stq	t0, 0(pv)
	# assignment
	ldq	t0, _var_tmp
	lda	pv, _var_b
	stq	t0, 0(pv)
	# writeln
	ldq	a0, _var_b
	bsr	ra, __print_int
	ldq	t0, _var_i
	addq	t0, 1, t0
	lda	pv, _var_i
	stq	t0, 0(pv)
	br	zero, FOR2
ENDFOR3:
	# writeln
	lda	a0, STR4
	bsr	ra, __print_str
	bsr	ra, __print_newline
	mov	fp, sp
	ldq	ra, 24(sp)
	ldq	fp, 16(sp)
	lda	sp, 32(sp)
	# exit(0) via PALcode
	mov	zero, a0
	call_pal	0x0001

	.data
	.align 3

	# global variable: n (8 bytes)
	.globl	_var_n
_var_n:
	.space	8

	# global variable: a (8 bytes)
	.globl	_var_a
_var_a:
	.space	8

	# global variable: b (8 bytes)
	.globl	_var_b
_var_b:
	.space	8

	# global variable: tmp (8 bytes)
	.globl	_var_tmp
_var_tmp:
	.space	8

	# global variable: i (8 bytes)
	.globl	_var_i
_var_i:
	.space	8
STR1:
	.asciz	"Fibonacci sequence:"
STR4:
	.asciz	""

_fmt_int:
	.asciz	"%ld"
_fmt_int_in:
	.asciz	"%ld"
_newline:
	.asciz	"\n"