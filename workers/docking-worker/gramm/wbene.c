/*
===============================================================================
                                                                        WBENE.C
                                                             Energy calculation
                                                     Atom-atom step-function LJ
===============================================================================
*/
#include <string.h>

extern float xa[],ya[],za[],xi[],yi[],zi[],ra[][2];
extern int   inta[],intb[],rnber[][2];
extern char  atmnam[][2][4];

void wbene (int mbak,int npa,int npb,float rcc,float ro,float *ene)
{
float en,eni,rcc2,rcc22,raa,r2;
int   i,j,tra,trb,implica,implicb,ik,ikk;

      en=0.;
      eni=1.;              /* implicit sidechain overlap atom add if CB free */

      tra=trb=1; ik=0;  ikk=-1;

      if (rcc)  /*------------------------------ Potential range = Grid step */
        {
         rcc2 =rcc+rcc-0.33*rcc; rcc2 =rcc2 *rcc2;
         rcc22=rcc+rcc+0.66*rcc; rcc22=rcc22*rcc22;

         for (i=1; i<=npa; i++)
           {
            if (inta[i]==0) continue;
            ik++;
            for (j=1; j<=npb; j++)
              {
               if (intb[j]==0) continue;
               r2=(xa[i]-xi[j])*(xa[i]-xi[j])+
                  (ya[i]-yi[j])*(ya[i]-yi[j])+
                  (za[i]-zi[j])*(za[i]-zi[j]);

               if (r2 < rcc2)                       /* atoms i and j overlap */
                 {
                  if (mbak==2)
                    {                          /* Implicit sidechains LIGAND */
                     implicb=0;
                     if (j>1)
                       {
                        if (strncmp(atmnam[j][1]," CB ",4)==0) trb=0; /* triggers implicit or usual, always within interface (intb/a) check) because it has to overlap to be here */
                        else{if(rnber[j][1]!=rnber[j-1][1])trb=1;}
                        if (trb&&(strncmp(atmnam[j][1]," N  ",4)!=0)
                               &&(strncmp(atmnam[j][1]," CA ",4)!=0)
                               &&(strncmp(atmnam[j][1]," C  ",4)!=0)
                               &&(strncmp(atmnam[j][1]," O  ",4)!=0))implicb=1;
                       }
                                             /* Implicit sidechains RECEPTOR */
                     if (ikk!=ik) /* i changed (avoid redundant calculations)*/
                       {
                        implica=0;
                        if (i>1)
                          {
                           if (strncmp(atmnam[i][0]," CB ",4)==0) tra=0;
                           else{if(rnber[i][0]!=rnber[i-1][0])tra=1;}
                           if (tra&&(strncmp(atmnam[i][0]," N  ",4)!=0)
                               &&(strncmp(atmnam[i][0]," CA ",4)!=0)
                               &&(strncmp(atmnam[i][0]," C  ",4)!=0)
                               &&(strncmp(atmnam[i][0]," O  ",4)!=0))implica=1;
                           ikk=ik;
                          }
                       }
                     if (implicb||implica) en+=eni;
                     else                  en-=ro;
                    }
                  else en-=ro;
                 }
               else { if (r2 < rcc22) en+=1.; }     /* atoms i and j attract */
              }
           }
        }
      else  /*-------------------------------- Potential range = Atom radius */
        {
         for (i=1; i<=npa; i++)
           {
            if (inta[i]==0) continue;
            ik++;
            raa=ra[i][0];
            for (j=1; j<=npb; j++)
              {
               if (intb[j]==0) continue;
               raa+=ra[j][1];
               rcc2 =raa+raa-0.33*raa; rcc2 =rcc2 *rcc2;
               rcc22=raa+raa+0.66*raa; rcc22=rcc22*rcc22;

               r2=(xa[i]-xi[j])*(xa[i]-xi[j])+
                  (ya[i]-yi[j])*(ya[i]-yi[j])+
                  (za[i]-zi[j])*(za[i]-zi[j]);

               if (r2 < rcc2)                       /* atoms i and j overlap */
                 {
                  if (mbak==2)
                    {                          /* Implicit sidechains LIGAND */
                     implicb=0;
                     if (j>1)
                       {
                        if (strncmp(atmnam[j][1]," CB ",4)==0) trb=0; 
                        else{if(rnber[j][1]!=rnber[j-1][1])trb=1;}
                        if (trb&&(strncmp(atmnam[j][1]," N  ",4)!=0)
                               &&(strncmp(atmnam[j][1]," CA ",4)!=0)
                               &&(strncmp(atmnam[j][1]," C  ",4)!=0)
                               &&(strncmp(atmnam[j][1]," O  ",4)!=0))implicb=1;
                       }
                                             /* Implicit sidechains RECEPTOR */
                     if (ikk!=ik) /* i changed (avoid redundant calculations)*/
                       {
                        implica=0;
                        if (i>1)
                          {
                           if (strncmp(atmnam[i][0]," CB ",4)==0) tra=0;
                           else{if(rnber[i][0]!=rnber[i-1][0])tra=1;}
                           if (tra&&(strncmp(atmnam[i][0]," N  ",4)!=0)
                               &&(strncmp(atmnam[i][0]," CA ",4)!=0)
                               &&(strncmp(atmnam[i][0]," C  ",4)!=0)
                               &&(strncmp(atmnam[i][0]," O  ",4)!=0))implica=1;
                           ikk=ik;
                          }
                       }
                     if (implicb||implica) en+=eni;
                     else                  en-=ro;
                    }
                  else en-=ro;
                 }
               else { if (r2 < rcc22) en+=1.; }     /* atoms i and j attract */
              }
           }
        }
      *ene=en;
}
