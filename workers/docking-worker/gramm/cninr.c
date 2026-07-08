/*
===============================================================================
                                                                        CNINR.C
                                                              Constraints input
===============================================================================
*/
#include <stdio.h>
#include <string.h>

extern int   ier1;
extern FILE  *fopen(),*fcon,*fflog;

void cninr(char *name,int *conres,int *conwei_p,int *conwei_n,int *tri)
{
int   is,i,ncon,nres,cnfd;
char  lin[250],dummy[250],pnam[100],*tr,ch;

      fcon=fopen("rcon.gr","r");
      if (fcon==NULL)
        { fprintf(fflog,"\n*** ERROR IN OPENING rcon.gr\n"); ier1=1; return; }

      while (1)
        {
         tr=fgets(lin,200,fcon);                        /* read current line */
         if (tr==NULL) { *tri=EOF; return; }

         if (lin[0]=='#') continue;                               /* comment */

         is=sscanf(lin,"%s",dummy); if (is==EOF) continue;     /* empty line */

         if ((lin[0]=='P')&&(lin[1]=='R'))continue;/*PRE - SEARCH constraints*/

         if ((lin[0]=='I')&&(lin[1]=='N'))continue;/*IN  - SEARCH constraints*/

         if ((lin[0]=='P')&&(lin[1]=='O'))continue;/*POST- SEARCH constraints*/

         if ((lin[0]=='W')&&(lin[1]=='e'))                         /* Weight */
           { sscanf(lin,"%s%d%d",dummy,conwei_p,conwei_n); continue; }

         sscanf(lin,"%s%d",pnam,&ncon);
         if (strcmp(pnam,name)==0) 
           {
            for (i=1; i<=ncon; i++) 
              { fscanf(fcon,"%d%d",&nres,&cnfd); conres[nres]=cnfd; }
            fclose(fcon); return;
           }
        }
}