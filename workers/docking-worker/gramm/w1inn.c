/*
===============================================================================
                                                                        W1INN.C
                                                                 RES name input
===============================================================================
*/
#include <stdio.h>
#include <string.h>

extern int   ier1;
extern FILE  *fopen(),*finlist,*fflog;

void w1inn(int nit,int *tri,char *fmatch)
{
int   il,is;
char  lin[250],dummy[250],*tr;

      finlist=fopen("wlist.gr","r");
      if (finlist==NULL)
        { fprintf(fflog,"\n*** ERROR IN OPENING wlist.gr\n"); 
          ier1=1; return; }
      il=0;
      while (1)
        {
         tr=fgets(lin,200,finlist);                       /*read current line*/
         if(tr==NULL) { *tri=EOF; return; }

         if(lin[0]=='#') continue;                                /* comment */

         is=sscanf(lin,"%s",dummy); if (is==EOF) continue;      /*empty line */
              
                                                                /* data line */
         il++; if (il<=nit) continue;                 /* skip earlier record */
 
         sscanf(lin,"%s",fmatch);

         break;
        }
      fclose(finlist);
}
