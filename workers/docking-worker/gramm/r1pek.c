/*
===============================================================================
                                                                        R1PEK.C
                                    Peak search (multi) with radius of identity
===============================================================================
*/
void r1us5(int *,long);
 
extern float g[];
extern float ng3;
extern long  sh[],w1[],w2[],w3[],ino[];
extern long  NG2,NG2_2,NG2_3;
extern int   pk[];
 
void r1pek (int npr,long rii,long ir,long *ic,int *us)
{
long  i,iout,i1,j1,k1,s1,s2,iw,jw,kw,s,i1out,j1out,k1out;
int   ip,ipp,ip1,p,ig,fl;
 
      for (ip=1; ip<=npr; ip++)
        {
         p=-32000;
         for (i=1l; i< NG2_3; i+=2l)
           {
            ig=(int)(g[i]/ng3);
            if (p<ig)
              {
               s1=(i-1l)/2l;  s2=s1%(NG2_2/2l);                    /* Unpack */
               k1=s1/(NG2_2/2l)+1l;j1=s2/(NG2/2l)+1l;i1=s2%(NG2/2l)+1l;
 
/*------------------------------------------------- Check for previous peaks */
               if (ip>1)
                 {
                  fl=0; ip1=ip-1;
                  for (ipp=1; ipp<=ip1; ipp++)
                    {
                     iw=i1-w1[ipp]; jw=j1-w2[ipp]; kw=k1-w3[ipp];
                     s=iw*iw+jw*jw+kw*kw;
                     if (s<=rii) { fl=1; break; }
                    }
                  if (fl) continue;
                 }
/*---------------------------------------------------------------------------*/
               p=ig; iout=i; i1out=i1; j1out=j1; k1out=k1;
              }
           }
         *ic=(*ic)+1l;
         pk[(*ic)]=p; sh[(*ic)]=iout; ino[(*ic)]=ir;
         w1[ip]=i1out; w2[ip]=j1out; w3[ip]=k1out;
 
         if (us[0]&&us[33]) r1us5(us,iout);
        }
}
