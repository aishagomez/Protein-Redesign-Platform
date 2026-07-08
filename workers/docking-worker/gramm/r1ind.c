/*
===============================================================================
                                                                        R1IND.C
                                        Molecule coordinates input (REC format)
===============================================================================
*/
#include <stdio.h>
 
extern float x[],y[],z[];
extern int   ier1;
extern char  typat[][2][4];
extern FILE  *fopen(),*fin,*fflog;
 
void r1ind (char *fn,int m,int *np)
{
int   i,k;
char  dummy[81],t[5];
 
      fin=fopen(fn,"r");
      if (fin==NULL)
        { fprintf(fflog,"\n*** ERROR IN OPENING %s\n\n",fn); ier1=1; return; }
 
      fscanf(fin,"%s%d",dummy,np); fgets(dummy,80,fin);
 
      for (i=1; i<=(*np); i++)
        {
         fscanf(fin,"%s%s%s%s%s%f%f%f%s",dummy,dummy,t,dummy,
                dummy,&x[i],&y[i],&z[i],dummy);
         for (k=0; k<=3; k++) { if(t[k]=='_') t[k]=' '; typat[i][m][k]=t[k]; }
        }
      fclose(fin);
}
