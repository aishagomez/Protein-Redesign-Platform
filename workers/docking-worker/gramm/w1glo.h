/*
===============================================================================
                                                                        W1GLO.H
                                                               Global variables
===============================================================================

rrpot                         - residue-residue potential
xko,yko,zko                   - accumulated B mol coordinates for output
xao,yao,zao                   - accumulated A mol coordinates for output
xw,yw,zw,xaw,yaw,zaw          - temp arrays for sorting
lxko,lyko,lzko,lxao,lyao,lzao - temp arrays for parallel transfer
cmao,cmbo,cmbbo,cm            - accumulated  CM coordinates for output
energy                        - energy
-----------------------------------------------------------------------------*/

float rrpot[DIMR+2][DIMR+2];
float xko[DIMF+2][DIM1+1],yko[DIMF+2][DIM1+1],zko[DIMF+2][DIM1+1];
float xao[DIMF+2][DIM1+1],yao[DIMF+2][DIM1+1],zao[DIMF+2][DIM1+1];
float xw [DIMF+2][DIM1+1],yw [DIMF+2][DIM1+1],zw [DIMF+2][DIM1+1];
float xaw[DIMF+2][DIM1+1],yaw[DIMF+2][DIM1+1],zaw[DIMF+2][DIM1+1];
float xi[DIM1+2],yi[DIM1+2],zi[DIM1+2],xo[DIM1+2],yo[DIM1+2],zo[DIM1+2];
float xr[DIM1+2],yr[DIM1+2],zr[DIM1+2];
float xa[DIM1+2],ya[DIM1+2],za[DIM1+2],xb[DIM1+2],yb[DIM1+2],zb[DIM1+2];
float lxko[(long)(DIMF)*(long)(DIM1)+2l];
float lyko[(long)(DIMF)*(long)(DIM1)+2l];
float lzko[(long)(DIMF)*(long)(DIM1)+2l];
float lxao[(long)(DIMF)*(long)(DIM1)+2l];
float lyao[(long)(DIMF)*(long)(DIM1)+2l];
float lzao[(long)(DIMF)*(long)(DIM1)+2l];
float cmao[DIMF+2][4],cmbo[DIMF+2][4],cmbbo[DIMF+2][4],cmo[DIMF+2][4];
float al[DIMM+2],bl[DIMM+2],gl[DIMM+2],ul[DIMM+2],vl[DIMM+2],wl[DIMM+2];
int   inta[DIM1+2],intb[DIM1+2];
int   energy[DIMM+2];
FILE  *finm,*finlist,*fout;
