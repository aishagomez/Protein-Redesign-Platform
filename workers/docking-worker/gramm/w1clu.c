/*
===============================================================================
                                                                        W1CLU.C
                                                          Clustering of matches
===============================================================================
*/
#include "r1dim.h"

extern float xko[][DIM1+1],yko[][DIM1+1],zko[][DIM1+1];
extern float xk[],yk[],zk[];

void w1clu(int im,int nmo,int npb,float rclusll,int *clusl,int *cnew)
{
float xyz,lrms,lrmsmin;
int   i,imo,imomin;

      if (im==1) { *cnew=1; return; }

      lrmsmin=100000.; imomin=0;

      for (imo=1; imo<=nmo; imo++)
        {
         lrms=0.;
         for (i=1; i<=npb; i++)
           {
            xyz=(xko[imo][i]-xk[i])*(xko[imo][i]-xk[i])+
                (yko[imo][i]-yk[i])*(yko[imo][i]-yk[i])+
                (zko[imo][i]-zk[i])*(zko[imo][i]-zk[i]);
            lrms+=xyz;
           }
         lrms/=((float)npb);

         if ((lrms<rclusll)&&(lrms<lrmsmin)) { lrmsmin=lrms; imomin=imo; }
        }

      if (imomin) { clusl[imomin]++; *cnew=0; } else *cnew=1;
}
