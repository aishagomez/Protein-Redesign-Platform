/*
===============================================================================
                                                                        W1STA.C
                                              Scoring by statistical potentials
===============================================================================
*/
#include <string.h>
#include "r1dim.h"

extern float x_1[],y_1[],z_1[],xk[],yk[],zk[],rrpot[][DIMR+2];
extern int   resn[][2];
extern char  atmnam[][2][4],resnam[][2][4];

void w1sta(int scosta,int npa,int npb,float *en)
{
float rcc,rcc2,r2;
int   c1,c2,res1,res2,i,j;

                                       /* Check potential input and symmetry */
/*    if (im==1) { for (i=1; i<=20; i++) { printf("\n"); for (j=1; j<=20; j++)
        { printf("%5.1f ",rrpot[i][j]);
          if (rrpot[i][j]!=rrpot[j][i]) printf("\nERROR %d %d",i,j); }}
          printf("\n"); } return; */

/*--------------------------------------------------------------------- GSVB */
      if (scosta==1)
        {
         rcc=6.0;                                          /* CB-CB distance */

         rcc2=rcc*rcc;
         *en=0.;

         for (i=1; i<=npa; i++)
           {
            if ((strncmp(atmnam[i][0]," CB ",4)==0)||
               ((strncmp(atmnam[i][0]," CA ",4)==0)&&
                (strncmp(resnam[i][0]," GLY",4)==0)))
              {
               for (j=1; j<=npb; j++)
                 {
                  if ((strncmp(atmnam[j][1]," CB ",4)==0)||
                     ((strncmp(atmnam[j][1]," CA ",4)==0)&&
                      (strncmp(resnam[j][1]," GLY",4)==0)))
                    {
                     r2=(x_1[i]-xk[j])*(x_1[i]-xk[j])+
                        (y_1[i]-yk[j])*(y_1[i]-yk[j])+
                        (z_1[i]-zk[j])*(z_1[i]-zk[j]);
                     if (r2 < rcc2)
                       {
                        res1=resn[i][0]; res2=resn[j][1];
                        *en=(*en)+rrpot[res1][res2];
                       }
                    }
                 }
              }
           }
        }
/*----------------------------------------------------------------------- MJ */
// R-R COM (all atoms incl.backbone, Ca for Gly) <= 6.5A - do when read coord.
// Checking instead for CB-CB just to see...
      if (scosta==2)
        {
         rcc=6.5;                                                /* distance */

         rcc2=rcc*rcc;
         *en=0.;

         for (i=1; i<=npa; i++)
           {
            if ((strncmp(atmnam[i][0]," CB ",4)==0)||
               ((strncmp(atmnam[i][0]," CA ",4)==0)&&
                (strncmp(resnam[i][0]," GLY",4)==0)))
              {
               for (j=1; j<=npb; j++)
                 {
                  if ((strncmp(atmnam[j][1]," CB ",4)==0)||
                     ((strncmp(atmnam[j][1]," CA ",4)==0)&&
                      (strncmp(resnam[j][1]," GLY",4)==0)))
                    {
                     r2=(x_1[i]-xk[j])*(x_1[i]-xk[j])+
                        (y_1[i]-yk[j])*(y_1[i]-yk[j])+
                        (z_1[i]-zk[j])*(z_1[i]-zk[j]);
                     if (r2 < rcc2)
                       {
                        res1=resn[i][0]; res2=resn[j][1];
                        *en=(*en)+rrpot[res1][res2];
                       }
                    }
                 }
              }
           }
        }
}