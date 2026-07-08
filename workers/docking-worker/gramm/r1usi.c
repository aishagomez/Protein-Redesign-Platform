/*
===============================================================================
                                                                        R1USI.C
                                                          User parameters input
===============================================================================
*/
#include <stdio.h>
 
#define  SKIP   fgets(dummy,61,fin)
 
extern FILE *fopen(),*fin;
 
void r1usi (int *us)
{
int   i;
char  dummy[81];
 
      fin=fopen("rusr.gr","r");
      if (fin==NULL)
        { for (i=1; i<=100; i++) us[i]=0; return; }     /* rusr.gr is absent */
 
      SKIP;fscanf(fin,"%d",us); SKIP;                     /* activation flag */
      if (us[0])
        {
         for (i=1; i<=us[0]; i++)
           {
            SKIP;fscanf(fin,"%d",us+i); SKIP;
           }
        }
      fclose(fin);
}
