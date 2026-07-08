/*
===============================================================================
                                                                        W1VDW.C
                                                      Scoring by VDW potentials
===============================================================================
*/
#include <string.h>

extern float x_1[],y_1[],z_1[],xk[],yk[],zk[];
extern int   rnber[][2];
extern char  atmnam[][2][4];

void w1vdw(int scovdw,int npa,int npb,float *en)
{
float rcc,rcc2,rcc22,r2,rc_r,rc_a,eni,ro,weight;
int   i,j,tra,trb,implica,implicb,ik,ikk;

      weight=1.;                  /* weight in the sum of scoring potentials */

      eni=1.;              /* implicit sidechain overlap atom add if CB free */

      rcc=2.0; ro=2.7;
//    rcc=3.5; ro=3.8;
      rc_r=0.33; rc_a=0.66;           /* Rep-Atr range from R+R (in R units) */
/*    rc_r=1.; rc_a=0.; */                     /* values corr to old scoring */

      rcc2 =rcc+rcc-rc_r*rcc; rcc2 =rcc2 *rcc2; 
      rcc22=rcc+rcc+rc_a*rcc; rcc22=rcc22*rcc22;

      tra=trb=1; ik=0;  ikk=-1;
      for (i=1; i<=npa; i++)
        {
         ik++;
         for (j=1; j<=npb; j++)
           {
            r2=(x_1[i]-xk[j])*(x_1[i]-xk[j])+
               (y_1[i]-yk[j])*(y_1[i]-yk[j])+
               (z_1[i]-zk[j])*(z_1[i]-zk[j]);

            if (r2 < rcc2)                          /* atoms i and j overlap */
              {
               if (scovdw==2)
                 {                             /* Implicit sidechains LIGAND */
                  implicb=0;
                  if (j>1)
                    {
                     if (strncmp(atmnam[j][1]," CB ",4)==0) trb=0; /* bad CB, sidechain doesn't change */ 
                     else {if(rnber[j][1]!=rnber[j-1][1])trb=1;} /* new residue, trb assumes default value (change) */
                     if (trb&&(strncmp(atmnam[j][1]," N  ",4)!=0) /* mainchain doesn't change */
                            &&(strncmp(atmnam[j][1]," CA ",4)!=0)
                            &&(strncmp(atmnam[j][1]," C  ",4)!=0)
                            &&(strncmp(atmnam[j][1]," O  ",4)!=0))implicb=1;
                    }
                                             /* Implicit sidechains RECEPTOR */
                  if (ikk!=ik)    /*i changed (avoid redundant calculations) */
                    {
                     implica=0;
                     if (i>1)
                       {
                        if (strncmp(atmnam[i][0]," CB ",4)==0) tra=0;
                        else {if(rnber[i][0]!=rnber[i-1][0]) tra=1;}
                        if (tra&&(strncmp(atmnam[i][0]," N  ",4)!=0)
                               &&(strncmp(atmnam[i][0]," CA ",4)!=0)
                               &&(strncmp(atmnam[i][0]," C  ",4)!=0)
                               &&(strncmp(atmnam[i][0]," O  ",4)!=0))implica=1;
                        ikk=ik;
                       }
                    }
                  if (implicb||implica) *en=(*en)+eni;
                  else                  *en=(*en)-ro;
                 }
               else *en=(*en)-ro;
              }
            else { if (r2 < rcc22) *en=(*en)+1.; }  /* atoms i and j attract */
           }
        }
      *en=(*en)*weight;
}