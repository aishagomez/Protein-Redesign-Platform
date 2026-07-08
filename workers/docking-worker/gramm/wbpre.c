/*
===++==========================================================================
                                                                     WBPRE_01.C
                                                                  Preprocessing
===============================================================================
*/
#include <math.h>

extern float xa[],ya[],za[],xb[],yb[],zb[];
extern int   inta[],intb[];

void wbpre(int npa,int npb,float rcc,float devr,float devt,float *cmb)
{
float rl,rmb,matrad,reps,r,xl,yl,zl,xab,yab,zab;
int   l,la,lb;

/*---------------------------------------------------------- Center of mol.B */
      cmb[1]=cmb[2]=cmb[3]=0.;
      for (l=1; l<=npb; l++) { cmb[1]+=xb[l]; cmb[2]+=yb[l]; cmb[3]+=zb[l]; }
      cmb[1]/=((float)npb); cmb[2]/=((float)npb); cmb[3]/=((float)npb);

/*---------------------------------------------------------- Radius of mol.B */
      rmb=0.;
      for (l=1; l<=npb; l++)
        {
         xl=xb[l]-cmb[1]; yl=yb[l]-cmb[2]; zl=zb[l]-cmb[3];
         rl=(float)sqrt((double)(xl*xl+yl*yl+zl*zl));
         if (rmb<rl) rmb=rl;
        }
/*----------------------------------------------------- Radius for interface */
      if (rcc>=2.0) matrad=rcc; else matrad=2.;           /* Max atom radius */

      reps =   matrad + matrad                  /* sum of two max atom radii */
             + 0.66*matrad                              /* contact tolerance */
             + devt                                     /* translation shift */
             + (float)sin((double)(devr*0.017453))*rmb;    /* rotation shift */
      reps=reps*reps;

/*-------------------------------------------- Interface atoms determination */
      for (la=1; la<=npa; la++) inta[la]=0;
      for (lb=1; lb<=npb; lb++) intb[lb]=0;

      for (la=1; la<=npa; la++)
        {
         for (lb=1; lb<=npb; lb++)
           {
            xab=xa[la]-xb[lb]; yab=ya[la]-yb[lb]; zab=za[la]-zb[lb];
            r=xab*xab+yab*yab+zab*zab;
            if (r<=reps) { inta[la]=1; intb[lb]=1; }
           }
        }
}
