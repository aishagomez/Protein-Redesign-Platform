/*
===============================================================================
                                                                        C1IPD.C
                                                     Molecule coordinates input
                                                      Convertor from PDB format
===============================================================================
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "r1dim.h"

/* void c1tab(char *); */
int  c1atm(char *);
int  c1res(char *); /* ADD NEW RES TYPES IF NEEDED FOR STAT POTENTIAL */

extern float x[],y[],z[];
extern int   atmnbr[][2],rnber[][2],resn[][2],repr,ier1;
extern char  typat[][2][4],atmnam[][2][4],resnam[][2][4];
extern char  mmode[];
extern FILE  *fopen(),*fin,*fflog;

extern int   myProc, nProc;

void c1ipd (char *fn,char *ch,int m,int *np,int *us)
{
double value;
float xl,yl,zl;
int   si,k,nat,nre,tri,atnb,an,rn,rner,sl,i,ii,ats,at1,at2,slen;
char  t[50][50][4]/*t[10000]*/,buf[110],dummy[110],linename[110],tatt[10],trest[10];
char  subunit[10],nofres[10],ch1[50],ch2[50],str[1000],fnn[1000],dup[10];
char  *pdbd,sub;

      fin=fopen(fn,"r");
      if (fin==NULL)                    /* PDB file not in current directory */
        {                                             /* Check PDB directory */
         pdbd=getenv("GRAMMPDB");
         if (pdbd==NULL)
            { if(myProc==0) fprintf (fflog, "\n*** ERROR IN OPENING %s",fn);
              if(us[2]&&(myProc==0)) printf("\n*** ERROR IN OPENING %s",fn);
              ier1=1; return; }
         strcpy(fnn,pdbd); strcat(fnn,fn);
         fin=fopen(fnn,"r");
         if (fin==NULL) 
           { if(myProc==0) fprintf (fflog, "\n*** ERROR IN OPENING %s",fnn);
             if(us[2]&&(myProc==0)) printf("\n*** ERROR IN OPENING %s",fnn);
             ier1=1; return; }
        }
/*---------------------------------------------------- Identify the fragment */
      sl=strlen(ch); ats=0;
      for (i=0; i<sl; i++) { if (ch[i]=='-') ats=1; }

      if (ats==0) 
        { sub=ch[0]; if (sub=='*') sub=' '; }
      else
        {
         for (i=0; i<sl; i++) 
           { if (ch[i]!='-') ch1[i]=ch[i]; else { ch1[i]='\0'; break; }}
         at1=atoi(ch1);

         ii=0;
         for (i=0; i<sl; i++)
           { if ((ch[i]!='-')&&(ii==0)) continue; ch2[ii++]=ch[i+1]; }
         ch2[ii++]='\0';
         at2=atoi(ch2);
        }
/*--------------------------------------------------------- Initialize table */

      c1tab(t);            /* table of REC atom types for PDB atoms-residues */

/*----------------------------------------------------------------- Read PDB */
      nat=nre=0;
      while (1)                                                  
        {
         tri=fscanf(fin,"%s",linename); if (tri==EOF) break;
         if ((si=strcmp(linename,"ATOM"))==0)
           {
            fscanf(fin,"%d",&atnb); fgets(dummy,2,fin);    /* PDB at.number  */
            fgets(tatt, 5,fin);                            /* PDB at.name    */
            fgets(trest,5,fin);                            /* residue name   */
            fgets(subunit,3,fin);                          /* subunit        */

            if (((ats==0)&&((subunit[1]==sub)||(sub==' ')))|| /* check fragm.*/
                ((ats==1)&&((atnb>=at1)&&(atnb<=at2))))
              {
               fscanf(fin,"%d",&rner); fgets(dup,3,fin);
               fscanf(fin,"%f%f%f",&xl,&yl,&zl); fgets(dummy,80,fin);

               if ((rn=c1res(trest))==0)        continue; /* skip double atom*/
               if ((dup[0]=='2')||(dup[0]=='B'))continue; /* skip double res */
               if ((an=c1atm(tatt)) ==0)        continue; /* skip hydrogen   */
               if ((repr==2)&&(an!=11))         continue; /* skip non c-alpha*/

               nat++; if (an==11) nre++;                           /* ACCEPT */
               if (nat>(DIM1-2))                            /* check max.no. */
                 { fprintf(fflog,
                   "\n*** ERROR: too many atoms in %s (%s)\n",fn,ch);
                   if(us[2])
                   printf("\n*** ERROR: too many atoms in %s (%s)",fn,ch);
                   ier1=1; return; }
               if (nre>(DIM11-2))                            /* check max.no. */
                 { fprintf(fflog,
                   "\n*** ERROR: too many residues in %s (%s)\n",fn,ch);
                   if(us[2])
                   printf("\n*** ERROR: too many residues in %s (%s)",fn,ch);
                   ier1=1; return; }

               atmnbr[nat][m]=atnb;                        /* PDB at.number  */
               rnber [nat][m]=rner;                        /* residue number */
               for (k=0; k<=3; k++)
                 {
                  atmnam[nat][m][k]=tatt[k];               /* PDB at.name    */
                  resnam[nat][m][k]=trest[k];              /* residue name   */
                 }
/*---------------------------------------------------------------------------*/
               if (us[39]) { sprintf(buf,"%4d %c%c%c %c%c%c%c %c%c%c %c%c%c",
                    nat,tatt[1],tatt[2],tatt[3],t[an][rn-1][0],t[an][rn-1][1],
                    t[an][rn-1][2],t[an][rn-1][3],trest[1],trest[2],trest[3],
                    nofres[1],nofres[2],nofres[3]); fprintf(fflog,"\n%s",buf);
                    fprintf(fflog," %7.3f %7.3f %7.3f",xl,yl,zl); } 
/*---------------------------------------------------------------------------*/
               resn[nat][m]=rn;                            /* residue num ID */
               strncpy(typat[nat][m],t[an][rn-1],4);       /* atom type      */
               x[nat]=xl; y[nat]=yl; z[nat]=zl;            /* coordinates    */
              }
            else fgets(dummy,100,fin);
           }
         else fgets(dummy,100,fin);
        }
      if (nat==0)
        { fprintf(fflog,
             "\n*** ERROR: no atoms in %s fragment %s are selected\n\n",fn,ch);
          if(us[2])printf("\n*** ERROR:no atoms in %s fragm %s selectd",fn,ch);
             ier1=1; return; }

      *np=nat; fclose(fin);
}
