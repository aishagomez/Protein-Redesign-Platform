/*
===============================================================================
                                                                        R1IOV.C
                             List of residues from binding site input (overlap)
===============================================================================
*/
#include <stdio.h>
 
extern int   nuro[],nuron,ier1;
extern FILE *fopen(),*fin,*fflog;
 
void r1iov (void)
{
int   nur,tri;
char  dummy[110];
 
      fin=fopen("rovp.gr","r");
      if (fin==NULL)
        { fprintf(fflog,"\n*** ERROR IN OPENING rovp.gr\n\n"); ier1=1; return;}

      nuron=0;
      while (1)
        {
         tri=fscanf(fin,"%d",&nur); if (tri==EOF) break; fgets(dummy,100,fin);
         nuron++; nuro[nuron]=nur;
        }

      fclose(fin);
}
