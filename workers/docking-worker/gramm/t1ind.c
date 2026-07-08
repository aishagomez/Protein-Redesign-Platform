/*
===============================================================================
                                                                        T1IND.C
                                                                 Read templates
===============================================================================
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "r1dim.h"

void c1ipd(char *,char *,int,int *,int *);

extern float xtp[][DIM11][2],ytp[][DIM11][2],ztp[][DIM11][2],x[],y[],z[];
extern int   trnum[][DIM11][2],rnber[][2],nrt[][2],ier1;
extern char  tnam[][20],trnam[][DIM11][2][3],atmnam[][2][4],resnam[][2][4];
extern char  amode[];
extern FILE  *fopen(),*fin,*fflog;

extern int   myProc, nProc;    /*PRLL*/

void t1ind(char *fnn,int *ntp,int *us)
{
int   tri,np,i,ii,j,l,m;
char  fnn1[1000],ch[3],d[20];
char  *tenv;

/*--------------------------------------------------- Read path to templates */
      tenv=getenv("GRAMMTEMPLATES"); 
      if (tenv==NULL)
        { fprintf(fflog,"\n*** ERROR: environment variable GRAMMTEMPLATES");
          fprintf(fflog," is not defined\n\n"); ier1=1; return;             }

      strcpy(fnn,tenv);
      if (amode[0]=='f') strcat(fnn,"/full/");
      else               strcat(fnn,"/intr/");

/*-------------------------------------------------- Read names of templates */
      strcpy(fnn1,fnn); strcat(fnn1,"list");
      fin=fopen(fnn1,"r");
      if (fin==NULL) 
        { fprintf (fflog, "\n*** ERROR IN OPENING %s",fnn1); ier1=1; return; }
          
      *ntp=0;
      while (1)                                                  
        {
         tri=fscanf(fin,"%s",d); if (tri==EOF) break;
         *ntp=*ntp+1; strcpy(tnam[*ntp],d);
        }
      fclose(fin);

/*-------------------------------------------- Read coordinates of templates */
      if ((us[2])&&(myProc==0)) {fflush(stdout);printf("\nReading template ");}
      strcpy(ch,"*");
      for (i=1; i<=(*ntp); i++)
        {
         if ((us[2])&&(myProc==0)) { fflush(stdout); printf("%4d\b\b\b\b",i); }
         for (m=0; m<=1; m++)
           {
            strcpy(fnn1,fnn); strcat(fnn1,tnam[i]);
            if (m==0) strcat(fnn1,"_1.pdb"); else strcat(fnn1,"_2.pdb");
            c1ipd(fnn1,ch,m,&np,us); if (ier1) return;
            ii=0;
            for (l=1; l<=np; l++)
              {
               if (strncmp(atmnam[l][m]," CA ",4)!=0) continue;
               ii++;
               xtp[i][ii][m]=x[l]; ytp[i][ii][m]=y[l]; ztp[i][ii][m]=z[l];
               trnum[i][ii][m]=rnber[l][m];
               for (j=0; j<=2; j++) trnam[i][ii][m][j]=resnam[l][m][j+1];
              }
            nrt[i][m]=ii;
           }
        }
}