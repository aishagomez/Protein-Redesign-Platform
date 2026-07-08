/*
===============================================================================
                                                                        W1BAK.C
                                                                   Backtracking
===============================================================================
*/
#include <stdio.h>
#include "r1dim.h"

void wbpar(int,float *,float *,float *,float *);
void wbpre(int,int,float,float,float,float *);
void wbecr(int,int,int,float,float,float,float,float *,float *,int *);

extern float xao[][DIM1+1],yao[][DIM1+1],zao[][DIM1+1];
extern float xko[][DIM1+1],yko[][DIM1+1],zko[][DIM1+1];
extern float xa[],ya[],za[],xb[],yb[],zb[];
extern float cmao[][4],cmbo[][4],cmbbo[][4],cmo[][4];
extern int   inta[],intb[];
extern int   myProc, nProc;    /*PRLL*/

void w1bak(int mbak,int imo,int npa,int npb,int *energyo,int *ic,int *us)
{
float cm_b[5];
float en,rcc,ro,devr,devt;
int   i,it,nt;

      *ic=(*ic)+1;

      for (i=1; i<=npb; i++)                     /* Transfer to local arrays */
        { xb[i]=xko[imo][i]; yb[i]=yko[imo][i]; zb[i]=zko[imo][i]; }
      for (i=1; i<=npa; i++)
        { xa[i]=xao[imo][i]; ya[i]=yao[imo][i]; za[i]=zao[imo][i]; }

      if ((us[2]==1)&&(nProc==1)) printf("\b\b\b%3d",*ic);
      if ((us[2]==2)&&(nProc==1)) printf("\n%3d",*ic);

      nt=1;                           /* Trajectory has one step (temporary) */
      for (it=1; it<=nt; it++)                           /* TRAJECTORY steps */
        {
                                                               /* Parameters */
         wbpar(it,&rcc,&ro,&devr,&devt);
                                                            /* Preprocessing */
                   /* Recalculate CM and Radius B (change in flexible search)*/
         wbpre(npa,npb,rcc,devr,devt,cm_b);

/*------------------------------------------------------------------- SEARCH */

         wbecr(mbak,npa,npb,rcc,ro,devr,devt,cm_b,&en,us);

/*-------------------------------------------------------------------------- */
        }
      for (i=1; i<=npb; i++)                    /* Transfer to global arrays */
        { xko[(*ic)][i]=xb[i]; yko[(*ic)][i]=yb[i]; zko[(*ic)][i]=zb[i]; }
      for (i=1; i<=npa; i++)
        { xao[(*ic)][i]=xa[i]; yao[(*ic)][i]=ya[i]; zao[(*ic)][i]=za[i]; }
      energyo[(*ic)]=((int)en);


/* cma -  CM mol A (change in flex A */
/* cmb -  CM mol B initial (change when end A overlapped with initial A) */
/* cmbb - CM mol B b/site init(change when end A overlap with initial A) */
/* cm   - CM mol B predicted (full if us[41]=0 or b/site if us[41]=1 */
}
