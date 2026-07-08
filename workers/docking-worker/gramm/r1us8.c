/*
===============================================================================
                                                                        R1US8.C
                                                                    User module
                                                        Criterion 3, CAPRI-like
===============================================================================
*/
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "r1dim.h"

#define SKIP  fgets(dummy,100,fic)
#define SKIP1 while(1){fscanf(fic,"%c",&ch);if(ch=='=')break;}

extern float x[],y[],z[],x_1[],y_1[],z_1[];
extern float xko[][DIM1+1],yko[][DIM1+1],zko[][DIM1+1],xb[],yb[],zb[];
extern float tra[][4],trb[][4],ura[][10],urb[][10],tmsa[],tmsb[];
extern long  ind[];
extern int   wgic,ier1;
extern char  atmnam[][2][4];
extern FILE  *fopen(),*fic,*foc,*fok,*fflog;

static float rd,rdd,lcarmsmx,licarmsmx;
static int   cabi[DIM1],succes[12],suc[12],mrank;

void r1us8(char *mode,char *sejo,int num,int npa,int npb,char *name_a,
           char *name_b)
{
float xyz,lcarms,licarms;
int   i,j,im,sucrate,sc,nlca,nlica,imd,imd1;
char  ch,dummy[210];

      for (im=1; im<=num; im++)
        {
         if (im==1)
           {
            foc=fopen("3.cri","w");              /* Open output summary file */         
/*--------------------------------------------------------------- Parameters */

            for (i=1; i<=10; i++) suc[i]=0;               /* Success trigger */

            if (wgic==1)
              {
               fok=fopen("3-list.cri","w");/* Open output match by match file*/
               rd=8.;                                      /* CA-CA distance */
               rdd=rd*rd;

               for (i=1; i<=10; i++) succes[i]=0;

               fic=fopen("rcr3.gr","r");
               if (fic==NULL)
                 { fprintf(fflog,"\n*** ERROR in opening rcr3.gr\n\n");ier1=1;
                   return; }

               fgets(dummy,100,fic);fgets(dummy,100,fic);          /* header */

               SKIP1;fscanf(fic,"%d",&mrank);    SKIP;/* max nnat sucss rank */
               if (mrank>num) mrank=num;
               SKIP1;fscanf(fic,"%f",&lcarmsmx); SKIP;/* max nnat lig  CaRMS */
               SKIP1;fscanf(fic,"%f",&licarmsmx);SKIP;/* max nnat lig iCaRMS */

               fclose(fic);

               fprintf(fok,"\n  Rank  L-CaRMS  L-i-CaRMS");
               if (mode[0]=='t') fprintf(fok,"   TM-score");
              }
            fprintf(fok,"\n\n  %s-%s",name_a,name_b);

/*------------------------------------------ Experimental complex processing */

                                            /* Assign interface C-alpha on B */
            for (i=1; i<=npb; i++)
              {
               cabi[i]=0;
               if (strncmp(atmnam[i][1]," CA ",4)==0)
                 {
                  for (j=1; j<=npa; j++)
                    {
                     if (strncmp(atmnam[j][0]," CA ",4)==0)
                       {
                        xyz=(x_1[j]-x[i])*(x_1[j]-x[i])+
                            (y_1[j]-y[i])*(y_1[j]-y[i])+
                            (z_1[j]-z[i])*(z_1[j]-z[i]);
                        if (xyz<=rdd) { cabi[i]=1; break; }
                       }
                    }
                 }
              }
            if (mode[0]=='f')
              { for (i=1; i<=npb; i++) { xb[i]=x[i]; yb[i]=y[i]; zb[i]=z[i]; }}

            if ((mode[0]=='t')&&(sejo[0]=='j'))
              {
               imd1=ind[1];                                /* sorted match 1 */
               for (i=1; i<=npb; i++)   /* Move exper B to coord frame of A1 */
                 {
                  xb[i]=tra[imd1][1]+ura[imd1][1]*x[i]
                                    +ura[imd1][2]*y[i]
                                    +ura[imd1][3]*z[i];
                  yb[i]=tra[imd1][2]+ura[imd1][4]*x[i]
                                    +ura[imd1][5]*y[i]
                                    +ura[imd1][6]*z[i];
                  zb[i]=tra[imd1][3]+ura[imd1][7]*x[i]
                                    +ura[imd1][8]*y[i]
                                    +ura[imd1][9]*z[i];
                 }
              }
           }
         if ((mode[0]=='t')&&(sejo[0]=='s'))
           {
            imd=ind[im];                                     /* sorted match */
            for (i=1; i<=npb; i++) /* Move exper B to coordinate frame of An */
              {
               xb[i]=tra[imd][1]+ura[imd][1]*x[i]
                                +ura[imd][2]*y[i]
                                +ura[imd][3]*z[i];
               yb[i]=tra[imd][2]+ura[imd][4]*x[i]
                                +ura[imd][5]*y[i]
                                +ura[imd][6]*z[i];
               zb[i]=tra[imd][3]+ura[imd][7]*x[i]
                                +ura[imd][8]*y[i]
                                +ura[imd][9]*z[i];
              }
           }
/*------------------------------------------------------------------ MATCHES */
         if (im>mrank) return;

/*--------------------------------------------------------------------- RMSD */

/* When flexible A implemented, add overlap of new and old A */

         lcarms=licarms=0.; nlca=nlica=0; sc=0;
         for (i=1; i<=npb; i++)
           {
            if (strncmp(atmnam[i][1]," CA ",4)==0)
              {
               nlca++;
               xyz=(xko[im][i]-xb[i])*(xko[im][i]-xb[i])+
                   (yko[im][i]-yb[i])*(yko[im][i]-yb[i])+
                   (zko[im][i]-zb[i])*(zko[im][i]-zb[i]);
               lcarms+=xyz;

               if (cabi[i])
                 {
                  nlica++;
                  licarms+=xyz;
                 }
              }
           }
         lcarms /=((float)nlca ); lcarms =(float)sqrt((double)lcarms );
         licarms/=((float)nlica); licarms=(float)sqrt((double)licarms);

         if (lcarms<=lcarmsmx)
           { sc=1; if (suc[1]==0) { succes[1]+=1; suc[1]=1; }}
         if (licarms<=licarmsmx)
           { sc=1; if (suc[2]==0) { succes[2]+=1; suc[2]=1; }}

         fprintf(fok,"\n");
         if (sc) { fprintf(fok,"**"); sc=0; } else fprintf(fok,"  ");
         fprintf(fok,"%3d    %5.2f    %5.2f",im,lcarms,licarms);
         if (mode[0]=='t') fprintf(fok,"     %4.2f %4.2f",tmsa[im],tmsb[im]);

         if (im==mrank)
           {
            fprintf(foc,"\nSUCCESS RATE (%%)\n");
            fprintf(foc,"\nMax rank: %d",mrank);
            fprintf(foc,"\nNo.of complexes");
            if (mode[0]=='t') fprintf(foc," with templates");
            fprintf(foc,": %d\n",wgic);

            sucrate=(int)((float)(100*succes[1])/((float)wgic));
            fprintf(foc,"\nLigand-CaRMSD       (max %2.0fA) = %d",
                    lcarmsmx,sucrate);

            sucrate=(int)((float)(100*succes[2])/((float)wgic));
            fprintf(foc,"\nLigand-iface-CaRMSD (max %2.0fA) = %d",
                    licarmsmx,sucrate);

            fclose(foc);
           }
        }
}
