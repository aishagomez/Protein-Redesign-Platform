/*
===============================================================================
                                                                        CNPST.C
                                                        Post search constraints
===============================================================================
*/
#include <string.h>
#include "r1dim.h"

extern float x_1[],y_1[],z_1[],xk[],yk[],zk[];
extern int   rnber[][2];
extern char  atmnam[][2][4];

void cnpst(int *conresa,int *conresb,int conwei_p,int conwei_n,
           int npa,int npb,float *enc)
{
float r2;
int   iresa[DIM1+2],iresb[DIM1+2];
int   ene,i,j,ires;

      ene=0; for(i=1;i<=npa;i++) iresa[i]=0; for(j=1;j<=npb;j++) iresb[j]=0;

/*------------------------------------------------ Detect interface residues */
      for (i=1; i<=npa; i++)
        {
         if (strncmp(atmnam[i][0]," CA ",4)!=0) continue;
         for (j=1; j<=npb; j++)
           {
            if (strncmp(atmnam[j][1]," CA ",4)!=0) continue;
            r2=(x_1[i]-xk[j])*(x_1[i]-xk[j])+
               (y_1[i]-yk[j])*(y_1[i]-yk[j])+
               (z_1[i]-zk[j])*(z_1[i]-zk[j]);

            if (r2<64.) { iresa[i]=1; iresb[j]=1; }
           }
        }
/*------------------------------------ Count interface residues in the score */
      for (i=1; i<=npa; i++)
         { 
          if ((strncmp(atmnam[i][0]," CA ",4)==0)&&(iresa[i]))
            { 
             ires=rnber[i][0]; 
             if (conresa[ires]) ene+=(conwei_p*conresa[ires]);
             else               ene+=(conwei_n*conresa[ires]);
            } 
         }
      for (j=1; j<=npb; j++)
         { 
          if ((strncmp(atmnam[j][1]," CA ",4)==0)&&(iresb[j]))
            {
             ires=rnber[j][1];
             if (conresb[ires]) ene+=(conwei_p*conresb[ires]);
             else               ene+=(conwei_n*conresb[ires]);
            } 
         }

      *enc=(float)ene;
}