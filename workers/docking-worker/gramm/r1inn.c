/*
===============================================================================
                                                                        R1INN.C
                                       Molecules filenames input and processing
===============================================================================
*/
#include <stdio.h>
#include <string.h>

extern int   maxa,ier1;
extern char  mmode[],antip[];
extern FILE  *fopen(),*finn,*fflog;

void r1inn(int nit,int *tri,char *resn,char *fna,char *fnb,char *cha,char *chb,
           char *name_a,char *name_b,char *mf)
{
int   i,ia,ib,ii,is,il;
char  lin[250],dummy[250],*tr;

/*------------------------------------------------------------- Read rmol.gr */
      finn=fopen("rmol.gr","r");  
      if (finn==NULL)
        { fprintf(fflog,"\n*** ERROR IN OPENING rmol.gr\n\n"); 
          ier1=1; return;}

      il=0;
      while (1)
        {
         tr=fgets(lin,200,finn);                         /*read current line*/
         if(tr==NULL) { *tri=EOF; return; }

         if(lin[0]=='#') continue;                               /* comment */

         is=sscanf(lin,"%s",dummy); if (is==EOF) continue;     /*empty line */
              
                                                                /* data line */
         il++; if (il<=nit) continue;                   /* skip earlier pair */
 
         sscanf(lin,"%s%s%s%s%s%s",fna,cha,name_a,fnb,chb,name_b);
         if (mmode[0]=='h') 
            sscanf(lin,"%s%s%s%s%s%s%s%d",
            dummy,dummy,dummy,dummy,dummy,dummy,antip,&maxa);

         break;
        }
/*--------------------------------------------------- Build results filename */

      ia=strlen(name_a); ib=strlen(name_b); ii=-1;
      for(i=0;i<ia;i++) { ii++; resn[ii]=name_a[i];} ii++; resn[ii]='-';
      for(i=0;i<ib;i++) { ii++; resn[ii]=name_b[i];} 
      ii++; resn[ii]='.'; ii++; resn[ii]='r'; ii++; resn[ii]='e';
      ii++; resn[ii]='s'; ii++; resn[ii]='\0';

/*----------------------------------------- Detect input format (mol.A only) */

      ia=strlen(fna); 
      if ((fna[ia-3]=='r')&&(fna[ia-2]=='e')&&(fna[ia-1]=='c')) *mf='r';
      else *mf='p';
/*---------------------------------------------------------------------------*/
      fclose(finn);
}
