/*
===============================================================================
                                                                        R1FFW.C
                                           3D discrete Fourier transform (FFTW)
===============================================================================
*/
#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <fftw3.h>
#include "r1gen.h"

/* Get index of zero-offset 3D array stored in Fortran order
   i,j,k - indices, _li - first leading dimension, _lij - 
   - (first leadinding dimension * second leading dimension) */
#define INDEXF3Z(_i,_j,_k,_li,_lij) ((_i)+(_j)*(_li)+(_k)*(_lij))
/* same as above for unit-based array */
#define INDEXF3U(_i,_j,_k,_li,_lij) (((_i)-1)+((_j)-1)*(_li)+((_k)-1)*(_lij))

extern float g[];
extern long  NG2,NG2_2, NG2_3;
extern int   npx;

/* GRAMM original FFT routine was based on NRC complex-to-complex
transform. Therefore, g[] always stores data as complex numbers. In case
of purely real arrays (projections), they are stored with stride 2 (in the
real part of 'complex'). Thus, if we use real-to-complex transform instead,
there is always enough space in g[]: g is 2*N*N*N, while real-to-complex output
is 2*(N/2+1)*N*N. Same is for loop limits in 'r1mul', which multiplies results 
of two direct transforms. Also, g[] is stored in Fortran-order (first index
changes the fastest). For the output of direct transform, the order and packing
do not matter, since only element-by-element conjugate multiplication is done 
with it in GRAMM (in r1mul). The order and packing of the input to reverse 
transform are the same as created by direct transform. For input of direct 
transform and output of reverse transform, have to convert from/to GRAMM order
*/
static int _npx_last=0; /* value of npx that was used to initialize plans; used
                        to decide if reinitialize */
static int is_constructed = 0; /* 0-static data not initialized, 1-otherwise */
static fftwf_plan fft_plan, fft_plan_inv; /* plans initial.once per grid size*/

typedef fftwf_complex fft_complex;
typedef float fft_real;

void r1ffw_free()
{
  if(is_constructed)
    {
     fftwf_destroy_plan(fft_plan);
     fftwf_destroy_plan(fft_plan_inv);
    }
  _npx_last = 0;
  is_constructed = 0;
}

void r1ffw_init(fft_real* preal, fft_complex* pcompl)
{
  int rank = 3;

  int dim[3];

  dim[0] = npx; dim[1] = npx; dim[2] = npx;

  r1ffw_free();
  _npx_last = npx;

  /* Create 'plans' for forward and reverse transforms. 
     We don't use 'in place' transforms because it's not clear
     how to convert 'in place' the in/out data from/to format that
     is expected by GRAMM (see description above) */

  /* ATTENTION: if any alternative to FFTW_ESTIMATE is used,
     the g[] array will be overwritten by plan creation calls !!! */
  fft_plan     = fftwf_plan_dft_r2c(rank,dim,preal,pcompl,FFTW_ESTIMATE);
  fft_plan_inv = fftwf_plan_dft_c2r(rank,dim,pcompl,preal,FFTW_ESTIMATE);

  is_constructed = 1;
}
 
void r1ffw (int isign)
{
  int ldx,ldy, ldx2, ldy2;  /* leading dimensions of real and complex arrays */
  int ldx21, ldy21;                                 /* ldx*ldx2 and ldy*ldy2 */
  int i,j,k;
  int ind;
  fft_complex *pcompl;
  fft_real *preal;

  pcompl = (fft_complex*)(g+1); /* view g[] as zero-based complex array, 
                             "fftw_complex" is defined in FFTW library header*/
  preal = (fft_real*) (g+1);            /* view g[] as zero-based real array */
  assert(isign == 1 || isign == -1);
  ldx = npx+2;
  ldy = ldx/2;
  assert(ldx%2 == 0);
  ldx2 = npx;
  ldy2 = npx;
  ldx21 = ldx*ldx2;
  ldy21 = ldy*ldy2;
  /* sanity checks for boundary conditions */
  /* real data fits into g[] */
  assert(INDEXF3U(npx,npx,npx,ldx,ldx21) < NG2_3);
  /* complex data fits into g[] */
  assert(INDEXF3U(ldy,npx,npx,ldy,ldy21)*((fft_real)sizeof(fft_complex))/sizeof(fft_real)<NG2_3);

  if(npx != _npx_last) r1ffw_init(preal,pcompl);

  if(isign==1) {
    /* repack real data obtained from GRAMM into zero-based array with stride 1 */
    for(k = 1; k <= npx; k++) for(j = 1; j <= npx; j++) for(i = 1; i <= npx; i++) {
      preal[INDEXF3U(i,j,k,ldx,ldx21)] =  g[R(i,j,k)];
    }
    fftwf_execute(fft_plan);
  }
  else if(isign==-1) {
    /*fft_real divider = 1.0/(((fft_real)npx)*npx*npx);*/
    fft_real divider = 1.0;
    fftwf_execute(fft_plan_inv);
    /* repack real data obtained from fft to real data expected by GRAMM */
    /* iterate top-down to avoid overwriting elements during in-place repacking */ 
    for(k = npx; k >= 1; k--) for(j = npx; j >= 1; j--) for(i = npx; i >= 1; i--) {
      ind = R(i,j,k);
      g[ind]= preal[INDEXF3U(i,j,k,ldx,ldx21)];
      g[ind+1] = 0; /* clean up the imaginary part */
    }
  }
}
