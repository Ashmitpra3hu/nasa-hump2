/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     |
    \\  /    A nd           | www.openfoam.com
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/

#include "kOmegaSSTML2.H"
#include "fvcGrad.H"

namespace Foam
{
namespace RASModels
{

template<class BasicTurbulenceModel>
scalar kOmegaSSTML2<BasicTurbulenceModel>::productionFactor
(
    const vector& U,
    const tensor& gradU,
    const scalar S2,
    const scalar y,
    const scalar omega
) const
{
    const scalar uMag = max(mag(U), SMALL);
    const vector convective = gradU & U;
    const scalar decel = max(-(U & convective)/max(sqr(uMag), SMALL), scalar(0));
    const scalar apgSignal = decel/max(omega, SMALL);

    const scalar vortMag = sqrt(max(2.0*magSqr(skew(gradU)), SMALL));
    const scalar shearRatio = sqrt(max(S2, SMALL))/max(vortMag, SMALL);

    const scalar apgWidth = max(apgWidth_, 1.0e-6);
    const scalar shearWidth = max(shearWidth_, 1.0e-6);
    const scalar yWidth = max(yWidth_, 1.0e-6);

    const scalar apgActivation = 0.5*(1.0 + tanh((apgSignal - apg0_)/apgWidth));
    const scalar shearActivation = 0.5*(1.0 + tanh((shearRatio - shear0_)/shearWidth));
    const scalar yOffset = (y - yPeak_)/yWidth;
    const scalar yActivation = exp(-sqr(yOffset));

    scalar factor = 1.0 + amplitude_*apgActivation*shearActivation*yActivation;
    factor = min(factorMax_, max(factorMin_, factor));
    return factor;
}


template<class BasicTurbulenceModel>
tmp<volScalarField::Internal> kOmegaSSTML2<BasicTurbulenceModel>::Pk
(
    const volScalarField::Internal& G
) const
{
    auto tPk = kOmegaSST<BasicTurbulenceModel>::Pk(G);

    if (!mlCorrection_)
    {
        return tPk;
    }

    tmp<volTensorField> tGradU = fvc::grad(this->U_);
    const volScalarField tS2(this->S2(tGradU()));

    auto& pk = tPk.ref();
    const vectorField& U = this->U_.primitiveField();
    const tensorField& gradU = tGradU().primitiveField();
    const scalarField& s2 = tS2.primitiveField();
    const scalarField& y = this->y_.primitiveField();
    const auto& omega = this->omega_();

    forAll(pk, celli)
    {
        pk[celli] *= productionFactor(U[celli], gradU[celli], s2[celli], y[celli], omega[celli]);
    }

    return tPk;
}


template<class BasicTurbulenceModel>
tmp<volScalarField::Internal> kOmegaSSTML2<BasicTurbulenceModel>::GbyNu
(
    const volScalarField::Internal& GbyNu0,
    const volScalarField::Internal& F2,
    const volScalarField::Internal& S2
) const
{
    auto tGbyNu = kOmegaSST<BasicTurbulenceModel>::GbyNu(GbyNu0, F2, S2);

    if (!mlCorrection_)
    {
        return tGbyNu;
    }

    tmp<volTensorField> tGradU = fvc::grad(this->U_);

    auto& gByNu = tGbyNu.ref();
    const vectorField& U = this->U_.primitiveField();
    const tensorField& gradU = tGradU().primitiveField();
    const scalarField& s2 = S2;
    const scalarField& y = this->y_.primitiveField();
    const auto& omega = this->omega_();

    forAll(gByNu, celli)
    {
        gByNu[celli] *= productionFactor(U[celli], gradU[celli], s2[celli], y[celli], omega[celli]);
    }

    return tGbyNu;
}


template<class BasicTurbulenceModel>
kOmegaSSTML2<BasicTurbulenceModel>::kOmegaSSTML2
(
    const alphaField& alpha,
    const rhoField& rho,
    const volVectorField& U,
    const surfaceScalarField& alphaRhoPhi,
    const surfaceScalarField& phi,
    const transportModel& transport,
    const word& propertiesName,
    const word& type
)
:
    kOmegaSST<BasicTurbulenceModel>
    (
        alpha,
        rho,
        U,
        alphaRhoPhi,
        phi,
        transport,
        propertiesName,
        type
    ),
    mlCorrection_(this->coeffDict().template getOrDefault<Switch>("mlCorrection", true)),
    amplitude_(this->coeffDict().template getOrDefault<scalar>("amplitude", 0.0)),
    factorMin_(this->coeffDict().template getOrDefault<scalar>("factorMin", 1.0)),
    factorMax_(this->coeffDict().template getOrDefault<scalar>("factorMax", 1.8)),
    apg0_(this->coeffDict().template getOrDefault<scalar>("apg0", 0.03)),
    apgWidth_(this->coeffDict().template getOrDefault<scalar>("apgWidth", 0.02)),
    shear0_(this->coeffDict().template getOrDefault<scalar>("shear0", 0.9)),
    shearWidth_(this->coeffDict().template getOrDefault<scalar>("shearWidth", 0.20)),
    yPeak_(this->coeffDict().template getOrDefault<scalar>("yPeak", 0.018)),
    yWidth_(this->coeffDict().template getOrDefault<scalar>("yWidth", 0.012))
{
    if (type == typeName)
    {
        this->printCoeffs(type);
    }
}

} // End namespace RASModels
} // End namespace Foam
