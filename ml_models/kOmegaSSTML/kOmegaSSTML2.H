/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     |
    \\  /    A nd           | www.openfoam.com
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/

#ifndef kOmegaSSTML2_H
#define kOmegaSSTML2_H

#include "kOmegaSST.H"

namespace Foam
{
namespace RASModels
{

template<class BasicTurbulenceModel>
class kOmegaSSTML2
:
    public kOmegaSST<BasicTurbulenceModel>
{
protected:

    Switch mlCorrection_;

    scalar amplitude_;
    scalar factorMin_;
    scalar factorMax_;
    scalar apg0_;
    scalar apgWidth_;
    scalar shear0_;
    scalar shearWidth_;
    scalar yPeak_;
    scalar yWidth_;

    scalar productionFactor
    (
        const vector& U,
        const tensor& gradU,
        const scalar S2,
        const scalar y,
        const scalar omega
    ) const;

    virtual tmp<volScalarField::Internal> Pk
    (
        const volScalarField::Internal& G
    ) const;

    virtual tmp<volScalarField::Internal> GbyNu
    (
        const volScalarField::Internal& GbyNu0,
        const volScalarField::Internal& F2,
        const volScalarField::Internal& S2
    ) const;

public:

    typedef typename BasicTurbulenceModel::alphaField alphaField;
    typedef typename BasicTurbulenceModel::rhoField rhoField;
    typedef typename BasicTurbulenceModel::transportModel transportModel;

    TypeName("kOmegaSSTML2");

    kOmegaSSTML2
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

    virtual ~kOmegaSSTML2() = default;
};

} // End namespace RASModels
} // End namespace Foam

#ifdef NoRepository
    #include "kOmegaSSTML2.C"
#endif

#endif
