/*
===============================================================================
                                                                        W1IRS.C
                                                                 RES data input
===============================================================================
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "w1dim.h"

extern float x[],y[],z[],x_1[],y_1[],z_1[];
extern float al[],bl[],gl[],ul[],vl[],wl[];
extern int   energy[];
extern int   repr,wgic,ier1,ier2;
extern FILE  *fopen(),*finm,*fflog;

void c1ipd(char *,char *,int,int *,int *);

void w1irs(char *fmatch,int mtch_f,int mtch_l,char *sejo,char *imol,int *num,
           char *name_a,char *name_b,char *fna,char *fnb,char *cha,char *chb,
           int *npat,int *npbt,float *aai,float *bbi,float *ggi,int *us)
{
float a,b,g,u,v,w,ai,bi,gi;
int   npa,npb,l,tri1,trii,mi,en,cali,nm;
char  edr[910],cal[900],dummy[910];

      nm=0;
/*----------------------------------------------------- Read list of matches */
      finm=fopen(fmatch,"r");
      if (finm==NULL)
        {fprintf(fflog,"\n*** ERROR IN OPENING %s\n\n",fmatch); 
         ier1=1; return; }
/*------------------------------------------- Search for [molecules] section */
      while (1)
        {
         tri1=fscanf(finm,"%s",edr); trii=strcmp(edr,"[molecules]");
         if (tri1==EOF)
           {
            fprintf(fflog,"\n*** ERROR:[molecules] section not found");
            fprintf(fflog," in %s",fmatch); ier2=1; return;
           }
         if (trii==0) { fgets(dummy,100,finm); break; }
        }
      fscanf(finm,"%s%s%s%s%s%s%s",name_a,dummy,fna,dummy,cha,dummy,cal);
      fgets(dummy,100,finm);
      fscanf(finm,"%s%s%s%s%s%s%s",name_b,dummy,fnb,dummy,chb,dummy,cal);
      fgets(dummy,100,finm);
      if ((cali=strcmp(cal,"CA"))==0) repr=2; else repr=0;
/*----------------------------------------------------- Read mol.coord files */
      c1ipd(fna,cha,0,&npa,us); if(ier1)return;
      for(l=1;l<=npa;l++) {x_1[l]=x[l];y_1[l]=y[l];z_1[l]=z[l];}
      *npat=npa;

      c1ipd(fnb,chb,1,&npb,us); if(ier1)return;
      *npbt=npb;
/*-------------------------------------- Search for [initial_angles] section */
      while (1)
        {
         tri1=fscanf(finm,"%s",edr); trii=strcmp(edr,"[initial_angles]");
         if (tri1==EOF) { rewind(finm); ai=bi=gi=0; break; }
         if (trii==0) 
           { 
            fscanf(finm,"%f%f%f",&ai,&bi,&gi); fgets(dummy,100,finm); 
            break; 
           }
        }
/*----------------------------------------------- Search for [match] section */
      while (1)
        {
         tri1=fscanf(finm,"%s",edr); trii=strcmp(edr,"[match]");
         if (tri1==EOF)
           {
            fprintf(fflog,"\n*** ERROR: [match] section not found\n\n");
            ier1=1; return;
           }
         if (trii==0) { fgets(dummy,100,finm); break; }
        }
/*----------------------------------------------- Search for the first match */
      while (1)
        {
         tri1=fscanf(finm,"%d%d%f%f%f%f%f%f",&mi,&en,&a,&b,&g,&u,&v,&w);
         fgets(dummy,100,finm);
         if (tri1==EOF)
           {
            fprintf(fflog,"\n*** ERROR: match #%d not found\n\n",mtch_f);
            ier1=1; return;
           }
         if (mi==mtch_f) break;
        }
      nm++; energy[nm]=en;
      al[nm]=a; bl[nm]=b; gl[nm]=g; ul[nm]=u; vl[nm]=v; wl[nm]=w;
      if (mtch_l!=mtch_f)
        {
         while (1)
           {
            tri1=fscanf(finm,"%d%d%f%f%f%f%f%f",&mi,&en,&a,&b,&g,&u,&v,&w);
            fgets(dummy,100,finm);
            if (tri1==EOF)
              {
               fprintf(fflog,"\n*** ERROR: match #%d not found\n\n",
                       mtch_l); ier1=1; return;
              }
            nm++; energy[nm]=en;
            al[nm]=a; bl[nm]=b; gl[nm]=g; ul[nm]=u; vl[nm]=v; wl[nm]=w;
            if (nm>DIMM)                  /* Check no. of matches to process */
              {
               fprintf(fflog,"\n*** ERROR: the program cannot process ");
               fprintf(fflog,"more than %d matches at once\n\n",DIMM);
               ier1=1; return;
              }
            if (mi==mtch_l) break;              /* End of the requested list */
           }
        }
      wgic++;                                  /* counter of molecular pairs */
      *num=nm; *aai=ai, *bbi=bi; *ggi=gi;
      fclose(finm);
}
