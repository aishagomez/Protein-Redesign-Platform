/*
===============================================================================
                                                                        T1INP.C
                                                               Parameters input
===============================================================================
*/
#include <stdio.h>
#include "w1dim.h"

#define SKIP  fgets(dummy,100,fin)
#define SKIP1 while(1){fscanf(fin,"%c",&ch);if(ch=='=')break;}

extern int   ier1;
extern char  amode[];
extern FILE  *fopen(),*fin,*fflog;
 
void t1inp (float *tmscoa,float *tmscob,int *covera,int *coverb,int *maxmch,
            char *sejo)
{
char  dummy[110],ch;
 
      fin=fopen("tpar.gr","r");
      if (fin==NULL)
        { fprintf(fflog,"\n*** ERROR IN OPENING tpar.gr\n\n"); ier1=1; return;}

      SKIP1;fscanf(fin,"%s",amode);  SKIP;       /* alignment mode(full,intr)*/
      SKIP1;fscanf(fin,"%f",tmscoa); SKIP;       /* TM-score for A           */
      SKIP1;fscanf(fin,"%f",tmscob); SKIP;       /* TM-score for B           */
      SKIP1;fscanf(fin,"%d",covera); SKIP;       /* coverage for A           */
      SKIP1;fscanf(fin,"%d",coverb); SKIP;       /* coverage for B           */
      SKIP1;fscanf(fin,"%d",maxmch); SKIP;       /* no of matches to output  */
         if((*maxmch)>DIMF)
           { fprintf(fflog,"\n*** ERROR: too many matches to output\n");
             ier1=1; return; }
      SKIP1;fscanf(fin,"%s",sejo);   SKIP;    /* output file (separate/joint)*/
         if((sejo[0]!='s')&&(sejo[0]!='j'))
           { fprintf(fflog,"\n*** ERROR: illegal parameter '%s'\n",sejo);
             ier1=1; return; }

      fclose(fin);
}
