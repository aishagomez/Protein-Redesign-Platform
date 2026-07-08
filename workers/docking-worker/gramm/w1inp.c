/*
===============================================================================
                                                                        W1INP.C
                                                               Parameters input
===============================================================================
*/
#include <stdio.h>
#include "w1dim.h"
 
#define SKIP  fgets(dummy,100,fin)
#define SKIP1 while(1){fscanf(fin,"%c",&ch);if(ch=='=')break;}

extern int   ier1;
extern FILE *fopen(),*fin,*fflog;
 
void w1inp(int *mtch_f,int *mtch_l,int *scovdw,int *scosta,int *ctr,
           float *rclusl,int *mbak,int *maxmch,char *sejo)
{
char  dummy[110],ch;
 
      fin=fopen("wpar.gr","r");
      if (fin==NULL)
        { fprintf(fflog,"\n*** ERROR IN OPENING wpar.gr\n\n"); ier1=1; return;}

      *mtch_f=1;                           /* First scan match               */
      SKIP1;fscanf(fin,"%d",mtch_l); SKIP; /* Last  scan match               */
         if(((*mtch_l)-(*mtch_f)+1)>DIMM)
           { fprintf(fflog,"\n*** ERROR: too many scan matches\n");
             ier1=1; return; }
      SKIP1;fscanf(fin,"%d",scovdw); SKIP; /* Scoring vdw                    */
         if(*scovdw>2)
           { fprintf(fflog,"\n*** ERROR: unknown vdw scoring type\n");
             ier1=1; return; }
      SKIP1;fscanf(fin,"%d",scosta); SKIP; /* Scoring statistical            */
         if(*scosta>2)
           { fprintf(fflog,"\n*** ERROR: unknown statistical scoring type\n");
             ier1=1; return; }
      SKIP1;fscanf(fin,"%d",ctr);    SKIP; /* Constraints                    */
      SKIP1;fscanf(fin,"%f",rclusl); SKIP; /* Cluster low-res iRMS-Ca radius */
      SKIP1;fscanf(fin,"%d",mbak);   SKIP; /* Backtracking                   */
         if(*mbak>2)
           { fprintf(fflog,"\n*** ERROR: unknown backtracking type\n");
             ier1=1; return; }
      SKIP1;fscanf(fin,"%d",maxmch); SKIP; /* No of matches to output        */
         if((*maxmch)>DIMF)
           { fprintf(fflog,"\n*** ERROR: too many matches to output\n");
             ier1=1; return; }
      SKIP1;fscanf(fin,"%s",sejo);   SKIP; /* Output file (separate/joint)   */
         if((sejo[0]!='s')&&(sejo[0]!='j'))
           { fprintf(fflog,"\n*** ERROR: illegal parameter '%s'\n",sejo);
             ier1=1; return; }

      fclose(fin);
}
