	<nav>
		<ul class="noBulletsOnList nav noPaddingMargin">
			<li id="ln" onclick="toggleSubOptions('synth-ln')" ><a href='index.php?option=ln' >LN</a> </li>
			<li id="attacks" onclick="toggleSubOptions('attacks')"> <a>Attacks</a> </li>
			<li id="sub-ln" onclick="toggleSubOptions('sub-ln')" ><a>Sub-LN</a> </li>
			<li id="synth-ln" onclick="toggleSubOptions('synth-ln')" ><a href='index.php?option=synth-ln' >Synth-LN</a> </li>
		</ul>
		<div class="container"></div>
	</nav>



	<script>
		const container = document.querySelector(".container");
        var options = [
			{ "id": "ln", "sub-options": [], "already-clicked": false},
			{ "id": "attacks", "sub-options": ["sa", "b"], "already-clicked": false},
			{ "id": "sub-ln", "sub-options": ["e", "f", "g", "h", "i", "j"], "already-clicked": false},
			{ "id": "synth-ln", "sub-options": [], "already-clicked": false}
		];

        function getOptionIndex(optionId){
			for (let i = 0; i < options.length; i++)
    			if(options[i].id == optionId)
					return i;
			return -1;
		}
		
		function toggleSubOptions(optionId) {
			var optionIndex = getOptionIndex(optionId); 
			var resHTML = '';
			
			// if the button was already clicked then remove the suboptions
			if(options[optionIndex]['already-clicked']){
				container.innerHTML = resHTML; 
				for (let i = 0; i < options.length; i++)
					options[i]['already-clicked'] = false;
				return;
			}
			
			// create the sub-options section
			var subOptions = options[optionIndex]['sub-options'];
			resHTML += '<ul class="noBulletsOnList nav2 noPaddingMargin">';
			for (let i = 0; i < subOptions.length; i++)
				resHTML += '<li><a href="index.php?option='+ subOptions[i] +'" >'+subOptions[i]+'</a></li>'; 
			resHTML += '</ul';
			container.innerHTML += resHTML;

			options[optionIndex]['already-clicked'] = true;
		}

        // Function to clear the container when not hovering
        function clearElements(event) {
			var container = document.querySelector(".container");

			// Check if the mouse has truly left the container
			if (!container.contains(event.relatedTarget)) {
				container.innerHTML = ''; 
				for (let i = 0; i < options.length; i++)
					options[i]['already-clicked'] = false; 
			}
    	}
    </script>
	

