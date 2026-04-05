/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     |
    \\  /    A nd           | www.openfoam.com
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/

#ifndef kOmegaSSTML_H
#define kOmegaSSTML_H

#include "kOmegaSST.H"

namespace Foam
{
namespace RASModels
{

template<class BasicTurbulenceModel>
class kOmegaSSTML
:
    public kOmegaSST<BasicTurbulenceModel>
{
protected:

    Switch mlCorrection_;

    scalar amplitude_;
    scalar factorMin_;
    scalar factorMax_;
    scalar chi0_;
    scalar chiWidth_;
    scalar yPeak_;
    scalar yWidth_;

    virtual void correctNut(const volScalarField& S2);
    virtual void correctNut();

public:

    typedef typename BasicTurbulenceModel::alphaField alphaField;
    typedef typename BasicTurbulenceModel::rhoField rhoField;
    typedef typename BasicTurbulenceModel::transportModel transportModel;

    TypeName("kOmegaSSTML");

    kOmegaSSTML
    (
        const alphaField& alpha,
        const rhoField& rho,
        const volVectorField& U,
        const surfaceScalarField& alphaRhoPhi,
        const surfaceScalarField& phi,
        const transportModel& transport,
        const word& propertiesName = turbulenceModel::propertiesName,
        const word& type = typeName
    );

    virtual ~kOmegaSSTML() = default;
};

} // End namespace RASModels
} // End namespace Foam

#ifdef NoRepository
    #include "kOmegaSSTML.C"
#endif

#endif

