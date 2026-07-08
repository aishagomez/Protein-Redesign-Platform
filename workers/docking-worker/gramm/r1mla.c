/*
===============================================================================
                                                                        R1MLA.C
                                                          Molecule A processing
===============================================================================
*/
void r1dig(float,int,int,float,int,int);
void r1us1(int *,float *,float,int,int,int);
void r1fft(int);
void r1ffw(int);

extern float g[],g1[];
extern long  NG2_3;
extern int   nurtog,ctiv;
extern char  mmode[];
 
void r1mla (int npa,int hca,float *ro,float eta3,int *us)
{
float rad,roo,pmax;
long  i;
int   m,fl;
 
      m=0;                                                     /* Mol.A flag */
      nurtog=0;                  /* Toggle for nonbinding residues (overlap) */
 
      for (i=1l; i< NG2_3; i+=2l) { g[i]=g1[i]=0.;}
      for (i=2l; i<=NG2_3; i+=2l) { g[i]=g1[i]=0.;}
  
      roo=ro[2]-ro[4]; rad=0.; fl=0;                /* Molecule digitization */
      r1dig(rad,npa,hca,roo,m,fl);  

      for (i=1l; i< NG2_3; i+=2l) { g1[i]=g[i]; g[i]=ro[0]; }  
 
      roo=ro[5]-ro[4]; rad+=1.; hca+=1; fl=1;            /* Surface on layer */
      r1dig(rad,npa,hca,roo,m,fl);

      for (i=1l; i< NG2_3; i+=2l) { g1[i]=g[i]-g1[i]; g[i]=ro[0]; }  
 
      roo=ro[5];      rad+=1.; hca+=1; fl=1;            /* Surface out layer */
      r1dig(rad,npa,hca,roo,m,fl);  

      for (i=1l; i< NG2_3; i+=2l) g[i]-=g1[i];  

      if ((mmode[0]=='o')&&(ctiv))     /* Overlap (gray) non-cumulative core */
        {
         roo=ro[2]; rad=0; hca-=1; ctiv=0;
         r1dig(rad,npa,hca,roo,m,fl);
         ctiv=1;
        }
/*---------------------------------------------------- Projection processing */
/*      pmax=0.;                                                             */
/*      for (i=1l; i< NG2_3; i+=2l) { if (pmax<g[i]) pmax=g[i]; }            */
/*      for (i=1l; i< NG2_3; i+=2l)                                          */
/*        {                                                                  */
/*         if (g[i]==0.) continue;                    */       /* background */
/*         if (g[i] <0.) { g[i+1]=g[i]; continue; }   */       /*   interior */
/*         g[i+1]=pmax-g[i];                          */       /*    surface */
/*        }                                                                  */
/*---------------------------------------------------------------------------*/
      if (us[0]&&us[3]) r1us1(us,ro,eta3,0,0,0);

      if (us[0]&&us[51]) r1fft(1); else r1ffw(1);                     /* FFT */

      for (i=1l; i< NG2_3; i+=2l) { g1[i]= g[i];g[i]=ro[0];} /* Pipe & conjg */
      for (i=2l; i<=NG2_3; i+=2l) { g1[i]=-g[i];g[i]=0.;}
}
