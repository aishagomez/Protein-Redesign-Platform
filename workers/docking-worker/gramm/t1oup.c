/*
===============================================================================
                                                                        T1OUP.C
           Put molecules A&B in predicted positions and assign re-scored values
===============================================================================
*/
#include <stdio.h>
#include <string.h>
#include "r1dim.h"

extern float x[],y[],z[],x_1[],y_1[],z_1[];
extern float xao[][DIM1+1],yao[][DIM1+1],zao[][DIM1+1];
extern float xko[][DIM1+1],yko[][DIM1+1],zko[][DIM1+1];
extern float xk[],yk[],zk[];
extern float wf1[],wf2[],wf3[],wf4[];
extern float tra[][4],trb[][4],ura[][10],urb[][10];
extern float rmsda[],rmsdb[],tmsa[],tmsb[];
extern long  ind[];
extern int   wi1[],wi2[],wi3[],wi4[];
extern int   seqa[],seqb[],cova[],covb[];
extern char  tna[][20],tnb[][20];
extern char  wc1[][20],wc2[][20];
extern FILE  *fflog;

void t1oup(int nmo,int nt,int npa,int npb,char *sejo)
{
float a,b,c,d,e,f,g,h,k,det,v11,v12,v13,v21,v22,v23,v31,v32,v33;
int   imo,imd,imd1,i;

/* -------------------------------- Put molecules A&B in predicted positions */
      for (imo=1; imo<=nmo; imo++)
        {
         imd=ind[imo];                                       /* sorted index */
         for (i=1; i<=npa; i++)
           {
            xao[imo][i]=tra[imd][1]+ura[imd][1]*x_1[i]
                                   +ura[imd][2]*y_1[i]
                                   +ura[imd][3]*z_1[i];
            yao[imo][i]=tra[imd][2]+ura[imd][4]*x_1[i]
                                   +ura[imd][5]*y_1[i]
                                   +ura[imd][6]*z_1[i];
            zao[imo][i]=tra[imd][3]+ura[imd][7]*x_1[i]
                                   +ura[imd][8]*y_1[i]
                                   +ura[imd][9]*z_1[i];
           }
         for (i=1; i<=npb; i++)
           {
            xko[imo][i]=trb[imd][1]+urb[imd][1]*x[i]
                                   +urb[imd][2]*y[i]
                                   +urb[imd][3]*z[i];
            yko[imo][i]=trb[imd][2]+urb[imd][4]*x[i]
                                   +urb[imd][5]*y[i]
                                   +urb[imd][6]*z[i];
            zko[imo][i]=trb[imd][3]+urb[imd][7]*x[i]
                                   +urb[imd][8]*y[i]
                                   +urb[imd][9]*z[i];
            }
        }
      if ((sejo[0]=='s')||(nmo==1)) return;

/* --- Put all Models in position overlapping Model 1 Mol A by moving Bn using 
inverse matrix for An and then moving Bn using direct matrix for A1 */

      imd1=ind[1];                                         /* sorted match 1 */
      for (imo=2; imo<=nmo; imo++)                   /* start with 2nd match */
        {
         imd=ind[imo];                                       /* sorted index */
         for (i=1; i<=npa; i++)           /* put An in predicted A1 position */
           {
            xao[imo][i]=xao[1][i];
            yao[imo][i]=yao[1][i];
            zao[imo][i]=zao[1][i];
           }
         a=ura[imd][1]; b=ura[imd][2]; c=ura[imd][3];/* direct matrix for An */
         d=ura[imd][4]; e=ura[imd][5]; f=ura[imd][6];
         g=ura[imd][7]; h=ura[imd][8]; k=ura[imd][9];

         det=a*(e*k-f*h)-b*(k*d-f*g)+c*(d*h-e*g);             /* determinant */
         if ((det>(-0.000001))&&(det<0.000001))
           { fprintf(fflog,
               "\n*** Rot.matrix for output cannot be inverted\n\n"); return; }
                                                    /* inverse matrix for An */
         v11= (e*k-f*h)/det; v12=-(b*k-c*h)/det; v13= (b*f-c*e)/det;
         v21=-(d*k-f*g)/det; v22= (a*k-c*g)/det; v23=-(a*f-c*d)/det;
         v31= (d*h-e*g)/det; v32=-(a*h-b*g)/det; v33= (a*e-b*d)/det;

         for (i=1; i<=npb; i++)     /* put Bn matched to original A position */
           {
            xk[i]= v11*(xko[imo][i]-tra[imd][1])
                  +v12*(yko[imo][i]-tra[imd][2])
                  +v13*(zko[imo][i]-tra[imd][3]);
            yk[i]= v21*(xko[imo][i]-tra[imd][1])
                  +v22*(yko[imo][i]-tra[imd][2])
                  +v23*(zko[imo][i]-tra[imd][3]);
            zk[i]= v31*(xko[imo][i]-tra[imd][1])
                  +v32*(yko[imo][i]-tra[imd][2])
                  +v33*(zko[imo][i]-tra[imd][3]);
           }
         for (i=1; i<=npb; i++)  /* put Bn matched to predicted A1 position */
           {
            xko[imo][i]=tra[imd1][1]+ura[imd1][1]*xk[i]
                                    +ura[imd1][2]*yk[i]
                                    +ura[imd1][3]*zk[i];
            yko[imo][i]=tra[imd1][2]+ura[imd1][4]*xk[i]
                                    +ura[imd1][5]*yk[i]
                                    +ura[imd1][6]*zk[i];
            zko[imo][i]=tra[imd1][3]+ura[imd1][7]*xk[i]
                                    +ura[imd1][8]*yk[i]
                                    +ura[imd1][9]*zk[i];
           }
        }
/* ------------------------------------------ Assign other re-sorted values */
      for (imo=1; imo<=nt; imo++)                                /* -> work */
        {
         wf1[imo]=rmsda[imo]; wf2[imo]=rmsdb[imo];
         wf3[imo]=tmsa[imo];  wf4[imo]=tmsb[imo];
         wi1[imo]=seqa[imo];  wi2[imo]=seqb[imo];
         wi3[imo]=cova[imo];  wi4[imo]=covb[imo];
         strcpy(wc1[imo],tna[imo]); strcpy(wc2[imo],tnb[imo]);
        }
      for (imo=1; imo<=nt; imo++)                                /* <- work */
        {
         imd=ind[imo];
         rmsda[imo]=wf1[imd]; rmsdb[imo]=wf2[imd];
         tmsa[imo] =wf3[imd]; tmsb[imo] =wf4[imd];
         seqa[imo] =wi1[imd]; seqb[imo] =wi2[imd];
         cova[imo] =wi3[imd]; covb[imo] =wi4[imd];
         strcpy(tna[imo],wc1[imd]); strcpy(tnb[imo],wc2[imd]);
        }
}