/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     |
    \\  /    A nd           | www.openfoam.com
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/

#include "kOmegaSSTML.H"
#include "fvcGrad.H"
#include "fvOptions.H"

namespace Foam
{
namespace RASModels
{

template<class BasicTurbulenceModel>
void kOmegaSSTML<BasicTurbulenceModel>::correctNut(const volScalarField& S2)
{
    kOmegaSSTBase<eddyViscosity<RASModel<BasicTurbulenceModel>>>::correctNut(S2);

    if (mlCorrection_)
    {
        const scalar chiFloor = 1.0e-12;
        const scalar chiWidth = max(chiWidth_, 1.0e-6);
        const scalar yWidth = max(yWidth_, 1.0e-6);

        const scalarField& y = this->y_.primitiveField();
        const scalarField& nu = this->nu()().primitiveField();
        scalarField& nut = this->nut_.primitiveFieldRef();

        forAll(nut, celli)
        {
            const scalar chi = max(nut[celli]/max(nu[celli], SMALL), chiFloor);
            const scalar chiActivation =
                0.5*(1.0 + tanh((log(chi) - log(max(chi0_, chiFloor)))/chiWidth));
            const scalar yOffset = (y[celli] - yPeak_)/yWidth;
            const scalar yActivation = exp(-sqr(yOffset));

            scalar factor = 1.0 + amplitude_*chiActivation*yActivation;
            factor = min(factorMax_, max(factorMin_, factor));
            nut[celli] *= factor;
        }

        this->nut_.correctBoundaryConditions();
        fv::options::New(this->mesh_).correct(this->nut_);
    }

    BasicTurbulenceModel::correctNut();
}


template<class BasicTurbulenceModel>
void kOmegaSSTML<BasicTurbulenceModel>::correctNut()
{
    correctNut(2*magSqr(symm(fvc::grad(this->U_))));
}


template<class BasicTurbulenceModel>
kOmegaSSTML<BasicTurbulenceModel>::kOmegaSSTML
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
    factorMin_(this->coeffDict().template getOrDefault<scalar>("factorMin", 0.85)),
    factorMax_(this->coeffDict().template getOrDefault<scalar>("factorMax", 1.60)),
    chi0_(this->coeffDict().template getOrDefault<scalar>("chi0", 3.0)),
    chiWidth_(this->coeffDict().template getOrDefault<scalar>("chiWidth", 1.0)),
    yPeak_(this->coeffDict().template getOrDefault<scalar>("yPeak", 0.015)),
    yWidth_(this->coeffDict().template getOrDefault<scalar>("yWidth", 0.010))
{
    if (type == typeName)
    {
        this->printCoeffs(type);
    }
}

} // End namespace RASModels
} // End namespace Foam

