.PHONY: validate preflight local daytona both
validate:
	bin/preflight all
preflight: validate
local:
	bin/run local
daytona:
	bin/run daytona
both:
	bin/run-both
