/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     |
    \\  /    A nd           | www.openfoam.com
     \\/     M anipulation  |
\*---------------------------------------------------------------------------*/

#include "turbulentTransportModels.H"
#include "kOmegaSSTML.H"
#include "kOmegaSSTML2.H"

makeRASModel(kOmegaSSTML);
makeRASModel(kOmegaSSTML2);
