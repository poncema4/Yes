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
	lda	t0, 10(zero)
	lda	pv, _var_n
	stq	t0, 0(pv)
	# assignment
	lda	t0, 64(zero)
	lda	t1, _var_arr
	lda	t2, 1(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 34(zero)
	lda	t1, _var_arr
	lda	t2, 2(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 25(zero)
	lda	t1, _var_arr
	lda	t2, 3(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 12(zero)
	lda	t1, _var_arr
	lda	t2, 4(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 22(zero)
	lda	t1, _var_arr
	lda	t2, 5(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 11(zero)
	lda	t1, _var_arr
	lda	t2, 6(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 90(zero)
	lda	t1, _var_arr
	lda	t2, 7(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 3(zero)
	lda	t1, _var_arr
	lda	t2, 8(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 55(zero)
	lda	t1, _var_arr
	lda	t2, 9(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	lda	t0, 77(zero)
	lda	t1, _var_arr
	lda	t2, 10(zero)
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# for i
	lda	t0, 1(zero)
	lda	pv, _var_i
	stq	t0, 0(pv)
FOR1:
	ldq	t0, _var_i
	ldq	t0, _var_n
	lda	t1, 1(zero)
	subq	t0, t1, t1
	cmplt	t1, t0, t2
	bne	t2, ENDFOR2
	# for j
	lda	t0, 1(zero)
	lda	pv, _var_j
	stq	t0, 0(pv)
FOR3:
	ldq	t0, _var_j
	ldq	t0, _var_n
	ldq	t1, _var_i
	subq	t0, t1, t1
	cmplt	t1, t0, t2
	bne	t2, ENDFOR4
	# if statement
	lda	t2, _var_arr
	ldq	t3, _var_j
	lda	t4, 1(zero)
	subq	t3, t4, t3
	s8addq	t3, t2, t2
	ldq	t0, 0(t2)
	lda	t5, _var_arr
	ldq	t7, _var_j
	lda	t0, 1(zero)
	addq	t7, t0, t6
	lda	t1, 1(zero)
	subq	t6, t1, t6
	s8addq	t6, t5, t5
	ldq	t1, 0(t5)
	cmplt	t1, t0, t0
	beq	t0, ELSE5
	# assignment
	lda	t0, _var_arr
	ldq	t1, _var_j
	lda	t2, 1(zero)
	subq	t1, t2, t1
	s8addq	t1, t0, t0
	ldq	t0, 0(t0)
	lda	pv, _var_tmp
	stq	t0, 0(pv)
	# assignment
	lda	t0, _var_arr
	ldq	t2, _var_j
	lda	t3, 1(zero)
	addq	t2, t3, t1
	lda	t4, 1(zero)
	subq	t1, t4, t1
	s8addq	t1, t0, t0
	ldq	t0, 0(t0)
	lda	t1, _var_arr
	ldq	t2, _var_j
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
	# assignment
	ldq	t0, _var_tmp
	lda	t1, _var_arr
	ldq	t0, _var_j
	lda	t1, 1(zero)
	addq	t0, t1, t2
	lda	t3, 1(zero)
	subq	t2, t3, t2
	s8addq	t2, t1, t1
	stq	t0, 0(t1)
ELSE5:
	ldq	t0, _var_j
	addq	t0, 1, t0
	lda	pv, _var_j
	stq	t0, 0(pv)
	br	zero, FOR3
ENDFOR4:
	ldq	t0, _var_i
	addq	t0, 1, t0
	lda	pv, _var_i
	stq	t0, 0(pv)
	br	zero, FOR1
ENDFOR2:
	# writeln
	lda	a0, STR7
	bsr	ra, __print_str
	bsr	ra, __print_newline
	# for i
	lda	t0, 1(zero)
	lda	pv, _var_i
	stq	t0, 0(pv)
FOR8:
	ldq	t0, _var_i
	ldq	t1, _var_n
	cmplt	t1, t0, t2
	bne	t2, ENDFOR9
	# writeln
	lda	t0, _var_arr
	ldq	t1, _var_i
	lda	t2, 1(zero)
	subq	t1, t2, t1
	s8addq	t1, t0, t0
	ldq	a0, 0(t0)
	bsr	ra, __print_int
	ldq	t0, _var_i
	addq	t0, 1, t0
	lda	pv, _var_i
	stq	t0, 0(pv)
	br	zero, FOR8
ENDFOR9:
	# writeln
	lda	a0, STR10
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

	# global variable: arr (80 bytes)
	.globl	_var_arr
_var_arr:
	.space	80

	# global variable: i (8 bytes)
	.globl	_var_i
_var_i:
	.space	8

	# global variable: j (8 bytes)
	.globl	_var_j
_var_j:
	.space	8

	# global variable: tmp (8 bytes)
	.globl	_var_tmp
_var_tmp:
	.space	8

	# global variable: n (8 bytes)
	.globl	_var_n
_var_n:
	.space	8
STR7:
	.asciz	"Sorted array:"
STR10:
	.asciz	""

_fmt_int:
	.asciz	"%ld"
_fmt_int_in:
	.asciz	"%ld"
_newline:
	.asciz	"\n"