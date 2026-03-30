from PIL import Image
import os

def load_image_data(filename):
    #check if file is in current working directory
    filepath = check_filename(filename)

    #Open image and get pixel data
    with Image.open(filepath) as img:
        return img.size,list(img.getdata())

def save_image_to_file(filename, image_dimension, image_data):
    try:
        #remove path from the inputted filename
        x=filename.index('/')
        while x!=-1:
            x=filename.index('/')
            filename = filename[x+1:]
    except:
        pass
    
    try:
        x=filename.index(chr(92))
        while x!=-1:
            x=filename.index(chr(92))
            filename = filename[x+1:]
    except:
        pass

    #create new image and put the data with encryptions, and save to ouput directory
    img = Image.new("RGB",image_dimension)
    img.putdata(image_data)

    current_working_DIR = os.path.dirname(__file__)

    img.save(current_working_DIR + "/output/modified_" + filename,format="PNG")

def get_data_to_encrypt(image_size):
    invalid = 1

    while invalid == 1:
        secret_key = input("Enter Key:")
        message = input("Enter Message:")
        invalid=0
        for char in secret_key:
            #check if key and message are valid
            if (char != 'u' and char != 'd') or len(secret_key) > 20 or len(secret_key) < 3 or len(message) > 1000 or len(message) < 10:
                invalid = 1
                print("Invalid Key/Message. Please Try again.")
                break

        for char in message:
            #check if characters from message are from 32 to 126 in ASCII table
            if ord(char)<32 and ord(char)>126:
                invalid = 1
                print("Invalid Key/Message. Please Try again.")
                break
        
        #get min no. of pixels needed and round up
        pixel_length = 6 + (8*(len(secret_key)+len(message)))/3
        if pixel_length != int(pixel_length): pixel_length = int(pixel_length)+1

        if pixel_length > image_size[0]*image_size[1]:
            invalid = 1
            print("Message and Key cannot fit in the image.")

    return (secret_key,message)

def encrypt_text(text, key):
    encrypted_text = ''
    shift_num=len(key)

    #Multiply key to accommodate all characters in the message
    key=((len(text)//len(key))+1)*key 
    key_ctr=0

    #encrypt text by characters
    for char in text:
            ascii_value=ord(char)
            if key[key_ctr]=='u':
                #check if shifted ASCII is within range
                if(ascii_value+shift_num>126):
                    ascii_value=31+((ascii_value+shift_num)%126)
                else:
                    ascii_value = ascii_value+shift_num
                    
            elif key[key_ctr]=='d':
                #check if shifted ASCII is within range
                if(ascii_value-shift_num<32):
                    ascii_value=127-(32%(ascii_value-shift_num))
                else:
                    ascii_value = ascii_value-shift_num
            encrypted_text = encrypted_text + chr(ascii_value)
            key_ctr = key_ctr+1
        
    return encrypted_text

def char_to_ascii(word):
    ascii_values=[]

    #Convert every character to ASCII table values, and add to a list
    for char in word:
        ascii_values.append(ord(char))
    return ascii_values

def ascii_to_binary(ascii_values):
    binary_values=[]

    #convert ASCII values to binary and add leading 0 bits until bit length is equal 8
    for num in ascii_values:
        bits = bin(num)[2:]
        while len(bits) != 8:
            bits = '0'+bits
        binary_values.append(bits)
        
    return binary_values

def encode_message(image_data, binary_key, binary_encrypted_message):
    bits_string=""

    #create a long string of the binary_key bits
    for byte in binary_key:
        bits_string = bits_string+byte

    #add delimiter bits
    bits_string = bits_string + "11111111"

    #add the binary_encrypted_message bits to the long string
    for byte in binary_encrypted_message:
        bits_string = bits_string+byte

    #add delimiter bits
    bits_string = bits_string + "11111111"

    counter = 0
    image_data_sequence=[]
    modified_image_data_list=[]

    #Create 1 list of RGB values of every pixel
    for pixel in image_data:
        for value in pixel:
            image_data_sequence.append(value)

    for value in image_data_sequence:
        #encode key and message to the image data
        if counter < len((bits_string)):
            #Adjust LSB according to the bits to be encoded
            if bits_string[counter] == '1':
                if value % 2 == 0:
                    #check if within range of RGB values (0-255)
                    if value + 1 > 255:
                        modified_image_data_list.append(value - 1)
                    else:
                        modified_image_data_list.append(value + 1)
                else:
                    modified_image_data_list.append(value)
            else:
                if value % 2 == 1: 
                    #check if within range of RGB values (0-255)
                    if value - 1 < 0:
                        modified_image_data_list.append(value + 1)
                    else:
                        modified_image_data_list.append(value - 1)
                else:
                    modified_image_data_list.append(value)
        #Copy the remaining image data
        else:
            modified_image_data_list.append(value)
        counter = counter + 1

    counter = 0
    pixel_tuple = ()
    modified_image_data=[]

    #Revert the the RGB values of pixels in to tuple in a list format
    while(counter < len(modified_image_data_list)):
        pixel_tuple = (modified_image_data_list[counter],modified_image_data_list[counter+1],modified_image_data_list[counter+2])
        modified_image_data.append(pixel_tuple)
        counter = counter + 3

    return modified_image_data

def decode_message(image_data):
    image_data_string=""

    #Create a long string of LSB of every RGB values of every pixel
    for pixel in image_data:
        for value in pixel:
            image_data_string = image_data_string + str(value%2)

    binary_key,binary_encrypted_message = [],[]
    delimiter_found,byte=0,""

    #Loop through the RGB values
    for bit in image_data_string:
        #create string of binary w/ 8 bits and find delimiter
        byte = byte+bit
        if len(byte)==8:
            if byte == "11111111":
                delimiter_found=delimiter_found+1
                byte=""
                #check if ALL delimiter are already found, exit loop for searching the delimiters
                if delimiter_found == 2:
                    break
                continue

            #if FIRST delimiter is not yet found, add the 8-bit binary string to list of binary_key
            if delimiter_found == 0:
                binary_key.append(byte)
                byte=""
            #if SECOND delimiter is not yet found, add the 8-bit binary string to list of binary_key
            elif delimiter_found == 1:
                binary_encrypted_message.append(byte)
                byte=""

    #Check if the 2 delimiters found,or key/message are found, return tuple of None if none
    if delimiter_found != 2 or binary_key == [] or binary_encrypted_message == []:
        return(None,None)
    
    return (binary_key,binary_encrypted_message)

def binary_to_ascii_string(binary_values):
    string=""

    #convert each 8-bit binary string to their ASCII table character values and compile into string
    for byte in binary_values:
        ascii_value = binary_to_decimal(byte, 8)
        string = string + chr(ascii_value)

    return string

def decrypt_text(encrypted_text, key):

        #Check if key is valid, return original text if not
        for char in key:
            if(char != "u" and char != "d") or len(key) > 20 or len(key) < 3 or len(encrypted_text) > 1000 or len(encrypted_text) < 10:
                print("Error: cannot decode message!")
                return encrypted_text

        #Check if message is valid, return original text if not
        for char in encrypted_text:
            if(ord(char) < 32 or ord(char) > 126):
                print("Error: cannot decode message!")
                return encrypted_text

        decrypted_text = ''
        shift_num=len(key)

        #Multiply key to accommodate all characters in the message
        key=((len(encrypted_text)//len(key))+1)*key
        key_ctr=0

        #decrypt text by characters
        for x in encrypted_text:
            ascii_value=ord(x)
            if key[key_ctr]=='d':
                 #check if shifted ASCII is within range
                if(ascii_value+shift_num>126):
                    ascii_value=31+((ascii_value+shift_num)%126)
                else:
                    ascii_value = ascii_value+shift_num
                    
            elif key[key_ctr]=='u':
                 #check if shifted ASCII is within range
                if(ascii_value-shift_num<32):
                    ascii_value=127-(32%(ascii_value-shift_num))
                else:
                    ascii_value = ascii_value-shift_num
            decrypted_text = decrypted_text + chr(ascii_value)
            key_ctr = key_ctr+1
       
        return decrypted_text

def save_file(filename,text):
    #remove the file extension in the filename for the name of the text file 
    if filename[len(filename)-4:len(filename)] == ".jpg": filename = filename[:len(filename)-4]
    elif filename[len(filename)-4:len(filename)] == "jpeg": filename = filename[:len(filename)-5]

    #remove directory/path in the inputted filename
    try:
        x=filename.index('/')
        while x!=-1:
            x=filename.index('/')
            filename = filename[x+1:]
    except:
        pass

    try:
        x=filename.index(chr(92))
        while x!=-1:
            x=filename.index(chr(92))
            filename = filename[x+1:]
    except:
        pass

    current_working_DIR = os.path.dirname(__file__)

    #open/create the text file and append the decoded message
    with open(current_working_DIR + "/output/" + filename + "_decoded_message.txt",'w') as text_file:
        text_file.write(text)

def binary_to_decimal(Bstr, n):
	#base case
	if n==0:
		return 0

	#recursion: gets bits starting from the last and calculate their value in decimal
	else:
		n=n-1
		bit=int(Bstr[n])
		return binary_to_decimal(Bstr, n) + bit*(2**(len(Bstr)-n-1))

def check_filename(filename):
    #gets the path of the current working directory; reference: https://docs.python.org/3/library/os.path.html
    current_working_DIR = os.path.dirname(__file__)
    try:
        with Image.open(current_working_DIR + '/' + filename) as image_file:
            filename = current_working_DIR + '/' + filename
    except:
       pass

    return filename

def main():
    mode=''
    while mode != "exit":
        mode = input("Select program mode: (encrypt/decrypt/exit):")
        if mode == "encrypt" or mode == "decrypt":
            invalid_file = 1
            while invalid_file == 1:
                filename = input("Enter image filename:")

                #check if file is in current working directory
                filepath = check_filename(filename)

                try:
                    with Image.open(filepath) as image_file:
                        image_format = filename[len(filename)-4:len(filename)]
                    if image_format == "jpeg" or image_format == ".jpg": invalid_file = 0
                    else: print("Invalid image file.")
                except: 
                    print("Invalid image file.")
            
            size,image_data=load_image_data(filename)
            
            if mode == "encrypt":
                secret_key_and_message = get_data_to_encrypt(size)
                encrypted_message = encrypt_text(secret_key_and_message[1], secret_key_and_message[0])

                binary_key = ascii_to_binary(char_to_ascii(secret_key_and_message[0]))
                binary_encrypted_message = ascii_to_binary(char_to_ascii(encrypted_message))

                modified_image_data = encode_message(image_data, binary_key, binary_encrypted_message)
                
                save_image_to_file(filename,size,modified_image_data)

            if mode == "decrypt":
                binary_decoded_data = decode_message(image_data)

                if binary_decoded_data == (None, None):
                    print("Error: cannot decode message!")
                    continue

                decrypt_key = binary_to_ascii_string(binary_decoded_data[0])
                decrypt_message = binary_to_ascii_string(binary_decoded_data[1])

                decrypted_text = decrypt_text(decrypt_message, decrypt_key)

                if(decrypt_message == decrypted_text):
                    continue
                
                save_file(filename,decrypted_text)

        elif mode == "exit":
            pass

        else: 
            print("Invalid input, choose a different item!")

    print("Thank you for using this program!")

if __name__ == '__main__':
    main()
