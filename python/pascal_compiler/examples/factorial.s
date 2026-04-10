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


	# ─── Procedure: factorial ───
factorial:
	# prologue: save RA, FP; set new FP
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	stq	fp, 16(sp)
	mov	sp, fp
	# assignment
	lda	t0, 1(zero)
	stq	t0, -16(fp)
	# while loop
WHILE1:
	ldq	t0, 16(fp)
	lda	t1, 1(zero)
	cmplt	t1, t0, t0
	beq	t0, ENDWHILE2
	# assignment
	ldq	t0, -16(fp)
	ldq	t1, 16(fp)
	mulq	t0, t1, t0
	stq	t0, -16(fp)
	# assignment
	ldq	t0, 16(fp)
	lda	t1, 1(zero)
	subq	t0, t1, t0
	stq	t0, 16(fp)
	br	zero, WHILE1
ENDWHILE2:
	# assignment
	ldq	t0, -16(fp)
	stq	t0, -8(fp)
	ldq	v0, -8(fp)
	# epilogue: restore RA, FP; return
	mov	fp, sp
	ldq	ra, 24(sp)
	ldq	fp, 16(sp)
	lda	sp, 32(sp)
	ret	zero, (ra), 1

	# ─── Main program entry point ───
	.globl	_start
_start:
	lda	sp, -32(sp)
	stq	ra, 24(sp)
	stq	fp, 16(sp)
	mov	sp, fp
	# writeln
	lda	a0, STR3
	bsr	ra, __print_str
	bsr	ra, __print_newline
	# for i
	lda	t0, 1(zero)
	lda	pv, _var_i
	stq	t0, 0(pv)
FOR4:
	ldq	t0, _var_i
	lda	t1, 10(zero)
	cmplt	t1, t0, t2
	bne	t2, ENDFOR5
	# assignment
	ldq	a0, _var_i
	bsr	ra, factorial
	mov	v0, t0
	lda	pv, _var_result
	stq	t0, 0(pv)
	# writeln
	ldq	a0, _var_result
	bsr	ra, __print_int
	ldq	t0, _var_i
	addq	t0, 1, t0
	lda	pv, _var_i
	stq	t0, 0(pv)
	br	zero, FOR4
ENDFOR5:
	# writeln
	lda	a0, STR6
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

	# global variable: i (8 bytes)
	.globl	_var_i
_var_i:
	.space	8

	# global variable: result (8 bytes)
	.globl	_var_result
_var_result:
	.space	8
STR3:
	.asciz	"Factorials 1..10:"
STR6:
	.asciz	""

_fmt_int:
	.asciz	"%ld"
_fmt_int_in:
	.asciz	"%ld"
_newline:
	.asciz	"\n"