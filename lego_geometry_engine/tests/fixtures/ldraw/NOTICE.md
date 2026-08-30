# LDraw regression fixture attribution

These fixture coordinates are extracted from the official LDraw Parts Library for regression testing only.

Attribution: The LDraw Parts Library and the authors named in each `.dat` header. The source files declare CC BY 4.0 or legacy CC BY 2.0-compatible LDraw Contributor Agreement terms. See https://www.ldraw.org/legal-info and the complete library's CAreadme/license files.

The `3005` dependency closure in this fixture now includes the official solid stud geometry (`stud.dat`, cylinder and disc primitives) so normal stud/anti-stud stacking is exercised against the same physical protrusion present in a complete LDraw library. Non-solid edge/conditional drawing lines may be omitted because the collision loader intentionally ignores LDraw line types 2 and 5.

The `3037` roof regression data remains a reduced slope shell containing the exact official polygon coordinates needed by the wall/slope collision tests; it is not a complete production representation of every decorative/stud primitive used by the full part.

This fixture as a whole is intentionally small and must not be used as a production LDraw installation. Production analysis must point `LDRAW_ROOT` at a complete official LDraw Parts Library.
